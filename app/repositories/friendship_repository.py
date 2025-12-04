from sqlalchemy.orm import Session
from uuid import UUID
from app.db.models.user import Friendship

def get_friendship(session: Session, user_id_1: UUID, user_id_2: UUID) -> Friendship | None:
    # order ids (user_id_1 < user_id_2) to be unique
    a, b = sorted([user_id_1, user_id_2])
    return (
        session.query(Friendship)
        .filter(Friendship.user_id_1 == a, Friendship.user_id_2 == b)
        .first()
    )

def create_friend_request(session: Session, from_id: UUID, to_id: UUID) -> Friendship:
    a, b = sorted([from_id, to_id])
    friendship = Friendship(
        user_id_1=a,
        user_id_2=b,
        status="pending",
    )
    session.add(friendship)
    session.flush()
    return friendship

def update_status(session: Session, friendship: Friendship, status: str) -> Friendship:
    from datetime import datetime
    friendship.status = status
    if status == "accepted":
        friendship.accepted_at = datetime.utcnow()
    session.flush()
    return friendship
