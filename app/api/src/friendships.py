# app/api/src/friendships.py

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.deps import get_db
from app.db.models.user import User
from app.repositories import friendship_repository as repo
from app.repositories.user_repository import get_user_by_email
from app.schemas.friend_request import FriendRequestByEmail
from app.schemas.friendship_response import FriendshipResponse
from app.services.suggest_friend_service import suggest_friends_for_user

router = APIRouter(prefix="/friends", tags=["friends"])

get_db_dependency = Depends(get_db)
current_user_dependency = Depends(get_current_user)


@router.post(
    "/requests/email",
    response_model=FriendshipResponse,
    status_code=status.HTTP_201_CREATED,
)
async def send_friend_request_by_email(
    payload: FriendRequestByEmail,
    db: AsyncSession = get_db_dependency,
    current_user: User = current_user_dependency,
):
    me_id: UUID = current_user.user_id
    me_email: str | None = current_user.email

    # Extra safety: email to self
    if me_email is not None and payload.email == me_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot send a friend request to yourself.",
        )

    try:
        async with db.begin():
            # 1. Find target user by email
            target = await get_user_by_email(db, payload.email)

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

            # 3. Check if friendship already exists (in any direction)
            existing = await repo.get_friendship(db, me_id, target_id)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Friendship already exists "
                    f"with status: {existing.status}",
                )

            # 4. Create new pending request (DB logic in repo)
            friendship = await repo.create_friend_request(db, me_id, target_id)

            # TODO: send real-time notification via WebSocket.

            return friendship

    except SQLAlchemyError as err:
        raise RuntimeError("Database error occurred") from err


@router.get(
    "/requests/incoming",
    response_model=list[FriendshipResponse],
)
async def list_incoming_requests(
    db: AsyncSession = get_db_dependency,
    current_user: User = current_user_dependency,
):
   
    me_id: UUID = current_user.user_id

    try:
        async with db.begin():
            requests = await repo.list_incoming_for_user(db, me_id)
            return requests

    except SQLAlchemyError as err:
        raise RuntimeError("Database error occurred") from err


@router.get(
    "/requests/sent",
    response_model=list[FriendshipResponse],
)
async def list_sent_requests(
    db: AsyncSession = get_db_dependency,
    current_user: User = current_user_dependency,
):
    
    me_id: UUID = current_user.user_id

    try:
        async with db.begin():
            requests = await repo.list_sent_for_user(db, me_id)
            return requests

    except SQLAlchemyError as err:
        raise RuntimeError("Database error occurred") from err


@router.post(
    "/requests/{other_user_id}/accept",
    response_model=FriendshipResponse,
)
async def accept_friend_request(
    other_user_id: UUID,
    db: AsyncSession = get_db_dependency,
    current_user: User = current_user_dependency,
):
    me_id: UUID = current_user.user_id

    try:
        async with db.begin():
            friendship = await repo.get_pending_between(
                db, me_id, other_user_id
            )

            if not friendship:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Pending friend request not found.",
                )

            friendship = await repo.accept_request(db, friendship)

            # TODO: notify both users via WebSocket.

            return friendship

    except SQLAlchemyError as err:
        raise RuntimeError("Database error occurred") from err


@router.post(
    "/requests/{other_user_id}/reject",
    status_code=status.HTTP_200_OK,
)
async def reject_friend_request(
    other_user_id: UUID,
    db: AsyncSession = get_db_dependency,
    current_user: User = current_user_dependency,
):
    me_id: UUID = current_user.user_id

    try:
        async with db.begin():
            friendship = await repo.get_pending_between(
                db, me_id, other_user_id
            )

            if not friendship:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Pending friend request not found.",
                )

            await repo.delete_request(db, friendship)

            # TODO: notify sender that the request was rejected.

            return {"detail": "Friend request rejected."}

    except SQLAlchemyError as err:
        raise RuntimeError("Database error occurred") from err


@router.get("/suggestions")
async def suggest_friends(
    current_user: User = current_user_dependency,
    db: AsyncSession = get_db_dependency,
):
    try:
        async with db.begin():
            suggestions = await suggest_friends_for_user(
                db, str(current_user.user_id)
            )
            return [
                {
                    "user_id": u.user_id,
                    "username": u.username,
                    "email": u.email,
                    "avatar_url": u.avatar_url,
                }
                for u in suggestions
            ]

    except SQLAlchemyError as err:
        raise RuntimeError("Database error occurred") from err
