import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.base import Base
from app.db.models.user import User
from app.db.deps import get_db
from app.core.deps import get_current_user
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine
import uuid
from datetime import datetime


SQLALCHEMY_DATABASE_URL = "sqlite:///./test_friend_suggestions.db"
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
    alice = create_test_user(db, email="alice@test.com", username="alice")
    bob = create_test_user(db, email="bob@test.com", username="bob")
    app.dependency_overrides[get_current_user] = get_current_user_override_factory(alice)
    with TestClient(app) as test_client:
        yield test_client, alice, bob
    app.dependency_overrides.pop(get_current_user, None)


def test_friend_suggestions_endpoint(client, db: Session):
    test_client, alice, bob = client
    # Create a third user: Carl
    carl = create_test_user(db, email="carl@test.com", username="carl")
    # Alice and Bob are friends
    test_client.post(
        "/friends/requests/by-email",
        json={"email": "bob@test.com"},
    )
    app.dependency_overrides[get_current_user] = get_current_user_override_factory(bob)
    test_client.post(f"/friends/requests/{alice.user_id}/accept")
    # Bob and Carl are friends
    app.dependency_overrides[get_current_user] = get_current_user_override_factory(bob)
    test_client.post(
        "/friends/requests/by-email",
        json={"email": "carl@test.com"},
    )
    app.dependency_overrides[get_current_user] = get_current_user_override_factory(carl)
    test_client.post(f"/friends/requests/{bob.user_id}/accept")
    # Alice should be suggested to add Carl
    app.dependency_overrides[get_current_user] = get_current_user_override_factory(alice)
    response = test_client.get("/friends/suggestions")
    assert response.status_code == 200
    suggestions = response.json()
    # Carl should be suggested to Alice
    assert any(u["email"] == "carl@test.com" for u in suggestions)
    # Bob is already a friend
    assert not any(u["email"] == "bob@test.com" for u in suggestions)
