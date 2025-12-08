from uuid import UUID
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models.user import Friendship


def _normalize_pair(user_id_1: UUID, user_id_2: UUID) -> tuple[UUID, UUID]:
    """
    Always store friendships with user_id_1 < user_id_2,
    so there is only one row per pair of users.
    """
    return tuple(sorted([user_id_1, user_id_2]))


def safe_commit(session: Session) -> None:
    """
    Commit helper: if commit fails, rollback and raise 500.
    """
    try:
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="A database error occurred. Please try again later.",
        )


#  Queries 

def get_friendship(
    session: Session, user_id_1: UUID, user_id_2: UUID
) -> Friendship | None:
    """
    Get friendship row between two users, regardless of order.
    """
    a, b = _normalize_pair(user_id_1, user_id_2)
    return (
        session.query(Friendship)
        .filter(Friendship.user_id_1 == a, Friendship.user_id_2 == b)
        .first()
    )


def create_friend_request(
    session: Session, from_id: UUID, to_id: UUID
) -> Friendship:
    """
    Create a new 'pending' friendship between two users.
    """
    a, b = _normalize_pair(from_id, to_id)
    friendship = Friendship(
        user_id_1=a,
        user_id_2=b,
        status="pending",
        created_at=datetime.utcnow(),
    )
    session.add(friendship)
    safe_commit(session)
    session.refresh(friendship)
    return friendship


def get_pending_between(
    session: Session, user_id_1: UUID, user_id_2: UUID
) -> Friendship | None:
    """
    Get a 'pending' friendship between two users, if any.
    """
    a, b = _normalize_pair(user_id_1, user_id_2)
    return (
        session.query(Friendship)
        .filter(
            Friendship.user_id_1 == a,
            Friendship.user_id_2 == b,
            Friendship.status == "pending",
        )
        .first()
    )


def list_pending_for_user(session: Session, user_id: UUID) -> list[Friendship]:
    """
    List all pending requests where this user is user_1 or user_2.
    """
    return (
        session.query(Friendship)
        .filter(
            Friendship.status == "pending",
            (Friendship.user_id_1 == user_id) | (Friendship.user_id_2 == user_id),
        )
        .all()
    )


def accept_request(session: Session, friendship: Friendship) -> Friendship:
    """
    Mark a pending request as accepted.
    """
    friendship.status = "accepted"
    friendship.accepted_at = datetime.utcnow()
    safe_commit(session)
    session.refresh(friendship)
    return friendship


def delete_request(session: Session, friendship: Friendship) -> None:
    """
    Delete a pending request (reject).
    """
    session.delete(friendship)
    safe_commit(session)
