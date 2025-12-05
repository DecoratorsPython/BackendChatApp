from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.core.deps import get_current_user
from app.db.models.user import User
from app.schemas.friend_request import FriendRequestByEmail
from app.schemas.friendship_response import FriendshipResponse

from app.repositories.user_repository import get_user_by_email
from app.repositories import friendship_repository as repo

router = APIRouter(prefix="/friends", tags=["friends"])


@router.post(
    "/requests/by-email",
    response_model=FriendshipResponse,
    status_code=status.HTTP_201_CREATED,
)
def send_friend_request_by_email(
    payload: FriendRequestByEmail,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Send a friend request to a user by email.
    """
    me_id: UUID = current_user.user_id
    me_email: str | None = current_user.email

    # Extra safety: email to self
    if me_email is not None and payload.email == me_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot send a friend request to yourself.",
        )

    # 1. Find target user by email
    target = get_user_by_email(db, payload.email)
    
    if not target:
        raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User with this email does not exist.",
    )
    target_id: UUID = target.user_id

    # 2. Prevent sending to self by id
    if me_id == target_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot send a friend request to yourself.",
        )

    # 3. Check if friendship already exists
    existing = repo.get_friendship(db, me_id, target_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Friendship already exists with status: {existing.status}",
        )

    # 4. Create new pending request (DB logic in repo)
    friendship = repo.create_friend_request(db, me_id, target_id)

    # TODO: send real-time notification via WebSocket.

    return friendship


@router.get(
    "/requests/incoming",
    response_model=list[FriendshipResponse],
)
def list_incoming_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all pending friend requests for the current user.
    """
    me_id: UUID = current_user.user_id
    requests = repo.list_pending_for_user(db, me_id)
    return requests


@router.post(
    "/requests/{other_user_id}/accept",
    response_model=FriendshipResponse,
)
def accept_friend_request(
    other_user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Accept a pending friend request between current_user and other_user_id.
    """
    me_id: UUID = current_user.user_id

    friendship = repo.get_pending_between(db, me_id, other_user_id)
    if not friendship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pending friend request not found.",
        )

    friendship = repo.accept_request(db, friendship)

    # TODO: notify both users via WebSocket.

    return friendship


@router.post(
    "/requests/{other_user_id}/reject",
    status_code=status.HTTP_200_OK,
)
def reject_friend_request(
    other_user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Reject a pending friend request (delete the row).
    """
    me_id: UUID = current_user.user_id

    friendship = repo.get_pending_between(db, me_id, other_user_id)
    if not friendship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pending friend request not found.",
        )

    repo.delete_request(db, friendship)

    # TODO: notify sender that the request was rejected.

    return {"detail": "Friend request rejected."}
