import os
import sys
import uuid
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# add project root to sys.path 
CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.main import app
from app.db.base import Base
from app.db.models.user import User, Friendship
from app.db.deps import get_db
from app.core.deps import get_current_user
from app.repositories.friendship_repository import _normalize_pair as normalize_pair



ALICE_EMAIL = "alice@test.com"
BOB_EMAIL = "bob@test.com"

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_friendships.db"


#  Test database setup 

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture()
def db() -> Session:
   
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


def override_get_db():
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


# Helpers

def create_test_user(db: Session, *, email: str, username: str) -> User:
    user = User(
        user_id=uuid.uuid4(),
        email=email,
        username=username,
        provider="google",
        provider_sub=f"{username}_sub",
        created_at=datetime.utcnow(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_current_user_override_factory(user: User):
   
    def _override():
        return user

    return _override


@pytest.fixture()
def client(db: Session):
    
    alice = create_test_user(db, email=ALICE_EMAIL, username="alice")
    bob = create_test_user(db, email=BOB_EMAIL, username="bob")

    app.dependency_overrides[get_current_user] = get_current_user_override_factory(alice)

    with TestClient(app) as test_client:
        yield test_client, alice, bob

    app.dependency_overrides.pop(get_current_user, None)


# Tests 

def test_send_friend_request_by_email_creates_pending_friendship(client, db: Session):
    test_client, alice, bob = client

    response = test_client.post(
        "/friends/requests/by-email",
        json={"email": BOB_EMAIL},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "pending"

    u1, u2 = normalize_pair(alice.user_id, bob.user_id)
    friendship = (
        db.query(Friendship)
        .filter(Friendship.user_id_1 == u1, Friendship.user_id_2 == u2)
        .one_or_none()
    )

    assert friendship is not None
    assert friendship.status == "pending"


def test_send_friend_request_to_self_is_not_allowed(client, db: Session):
    test_client, alice, _ = client

    response = test_client.post(
        "/friends/requests/by-email",
        json={"email": ALICE_EMAIL},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "You cannot send a friend request to yourself."


def test_cannot_send_duplicate_friend_request(client, db: Session):
    test_client, _, _ = client

    first = test_client.post(
        "/friends/requests/by-email",
        json={"email": BOB_EMAIL},
    )
    assert first.status_code == 201

    second = test_client.post(
        "/friends/requests/by-email",
        json={"email": BOB_EMAIL},
    )

    assert second.status_code == 400
    assert "Friendship already exists" in second.json()["detail"]


def test_accept_friend_request_marks_as_accepted(client, db: Session):
    test_client, alice, bob = client

    # Alice sends friend request to Bob
    r1 = test_client.post(
        "/friends/requests/by-email",
        json={"email": BOB_EMAIL},
    )
    assert r1.status_code == 201

    # Bob becomes current_user
    app.dependency_overrides[get_current_user] = get_current_user_override_factory(bob)

    # Bob accepts the friend request (other_user_id = Alice)
    response = test_client.post(
        f"/friends/requests/{alice.user_id}/accept",
    )

    
    app.dependency_overrides[get_current_user] = get_current_user_override_factory(alice)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "accepted"
    assert data["accepted_at"] is not None

    u1, u2 = normalize_pair(alice.user_id, bob.user_id)
    friendship = (
        db.query(Friendship)
        .filter(Friendship.user_id_1 == u1, Friendship.user_id_2 == u2)
        .one_or_none()
    )

    assert friendship is not None
    assert friendship.status == "accepted"
    assert friendship.accepted_at is not None


def test_reject_friend_request_deletes_row(client, db: Session):
    test_client, alice, bob = client

    r1 = test_client.post(
        "/friends/requests/by-email",
        json={"email": BOB_EMAIL},
    )
    assert r1.status_code == 201

    # Bob becomes current_user
    app.dependency_overrides[get_current_user] = get_current_user_override_factory(bob)

    response = test_client.post(
        f"/friends/requests/{alice.user_id}/reject",
    )

    # Switch back to Alice
    app.dependency_overrides[get_current_user] = get_current_user_override_factory(alice)

    assert response.status_code == 200
    assert response.json()["detail"] == "Friend request rejected."

    u1, u2 = normalize_pair(alice.user_id, bob.user_id)
    friendship = (
        db.query(Friendship)
        .filter(Friendship.user_id_1 == u1, Friendship.user_id_2 == u2)
        .one_or_none()
    )

    assert friendship is None
