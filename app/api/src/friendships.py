from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.db.deps import get_db
from app.core.deps import get_current_user # needs to be implemented
from app.db.models.user import User, Friendship
from app.schemas.friendship import (
    FriendRequestByEmail,
    FriendshipResponse,
)

router = APIRouter(prefix="/friends", tags=["friends"])


# Helpers DB 

def normalize_pair(a: UUID, b: UUID) -> tuple[UUID, UUID]:
    """
    Always store friendships with user_id_1 < user_id_2,
    so there is only one row per pair of users.
    """
    return tuple(sorted([a, b]))


def get_friendship(
    db: Session, user_id_1: UUID, user_id_2: UUID
) -> Friendship | None:
    u1, u2 = normalize_pair(user_id_1, user_id_2)
    return (
        db.query(Friendship)
        .filter(Friendship.user_id_1 == u1, Friendship.user_id_2 == u2)
        .first()
    )


def safe_commit(db: Session) -> None:
    """
    Small helper to keep commit error handling in one place.
    If commit fails, rollback and raise 500.
    """
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="A database error occurred. Please try again later.",
        )


#  Endpoints 

@router.post(
    "/requests/by-email",
    response_model=FriendshipResponse,
    status_code=status.HTTP_201_CREATED,
)
def send_friend_request_by_email(
    payload: FriendRequestByEmail,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Send a friend request to a user by email.
    """

    me_id: UUID = current_user.user_id

    # 1. Find target user by email
    target: User | None = (
        db.query(User).filter(User.email == payload.email).first()
    )
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with this email does not exist.",
        )

    target_id: UUID = target.user_id

    if me_id == target_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot send a friend request to yourself.",
        )

    # 2. Check if friendship already exists
    existing = get_friendship(db, me_id, target_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Friendship already exists with status: {existing.status}",
        )

    # 3. Create new friendship with 'pending' status
    u1, u2 = normalize_pair(me_id, target_id)
    friendship = Friendship(
        user_id_1=u1,
        user_id_2=u2,
        status="pending",
        created_at=datetime.utcnow(),
    )

    db.add(friendship)
    safe_commit(db)
    db.refresh(friendship)

    # TODO: send real-time notification via WebSocket here.
    # await ws_manager.send_to_user(target_id, {...})

    return friendship


@router.get(
    "/requests/incoming",
    response_model=list[FriendshipResponse],
)
def list_incoming_requests(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    List all pending friend requests where the current user is one of the two.
    Frontend can filter who is the sender/receiver if needed.
    """
    me_id: UUID = current_user.user_id

    requests = (
        db.query(Friendship)
        .filter(
            Friendship.status == "pending",
            (Friendship.user_id_1 == me_id) | (Friendship.user_id_2 == me_id),
        )
        .all()
    )

    return requests


@router.post(
    "/requests/{other_user_id}/accept",
    response_model=FriendshipResponse,
)
def accept_friend_request(
    other_user_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Accept a pending friend request between current_user and other_user_id.
    """
    me_id: UUID = current_user.user_id
    u1, u2 = normalize_pair(me_id, other_user_id)

    friendship: Friendship | None = (
        db.query(Friendship)
        .filter(
            Friendship.user_id_1 == u1,
            Friendship.user_id_2 == u2,
            Friendship.status == "pending",
        )
        .first()
    )

    if not friendship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pending friend request not found.",
        )

    friendship.status = "accepted"
    friendship.accepted_at = datetime.utcnow()

    safe_commit(db)
    db.refresh(friendship)

    # TODO: notify both users via WebSocket if needed.

    return friendship


@router.post(
    "/requests/{other_user_id}/reject",
    status_code=status.HTTP_200_OK,
)
def reject_friend_request(
    other_user_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Reject a pending friend request.
    We simply delete the row here.
    """
    me_id: UUID = current_user.user_id
    u1, u2 = normalize_pair(me_id, other_user_id)

    friendship: Friendship | None = (
        db.query(Friendship)
        .filter(
            Friendship.user_id_1 == u1,
            Friendship.user_id_2 == u2,
            Friendship.status == "pending",
        )
        .first()
    )

    if not friendship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pending friend request not found.",
        )

    db.delete(friendship)
    safe_commit(db)

    # TODO: notify sender that the request was rejected (optional).

    return {"detail": "Friend request rejected."}
