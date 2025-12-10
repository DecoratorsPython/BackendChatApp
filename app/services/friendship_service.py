from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import SessionLocal
from app.repositories import friendship_repository


async def send_friend_request(
    db: AsyncSession, current_user_id: UUID, target_user_id: UUID
):
    if current_user_id == target_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot send a friend request to yourself.",
        )

    existing = await friendship_repository.get_friendship(
        db, current_user_id, target_user_id
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A relationship with status "
            f"'{existing.status}' already exists.",
        )

    friendship = await friendship_repository.create_friend_request(
        db, current_user_id, target_user_id
    )
    return friendship


async def is_friend(user_a: str, user_b: str) -> bool:
    async with SessionLocal() as session:
        try:
            async with session.begin():
                friendship = await friendship_repository.get_friendship(
                    session, user_a, user_b
                )

                return (
                    friendship is not None and friendship.status == "accepted"
                )

        except SQLAlchemyError as err:
            raise RuntimeError("Database error occurred") from err
