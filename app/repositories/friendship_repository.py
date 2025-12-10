# app/repositories/friendship_repository.py

from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy import or_

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import Friendship, User
from app.db.session import SessionLocal



async def get_friendship(
    session: AsyncSession, user_id_1: UUID, user_id_2: UUID
) -> Friendship | None:
    
    try:
        statement = (
            select(Friendship)
            .where(
                (
                    (Friendship.user_id_1 == user_id_1)
                    & (Friendship.user_id_2 == user_id_2)
                )
                | (
                    (Friendship.user_id_1 == user_id_2)
                    & (Friendship.user_id_2 == user_id_1)
                )
            )
            .limit(1)
        )

        result = await session.execute(statement)
        friendship = result.scalars().first()

        return friendship

    except SQLAlchemyError as err:
        raise RuntimeError("Database error occurred") from err


async def create_friend_request(
    session: AsyncSession, from_id: UUID, to_id: UUID
) -> Friendship:
   
    try:
        friendship = Friendship(
            user_id_1=from_id,
            user_id_2=to_id,
            status="pending",
            created_at=datetime.now(timezone.utc),
        )

        session.add(friendship)
        await session.flush()
        await session.refresh(friendship)

        return friendship

    except SQLAlchemyError as err:
        raise RuntimeError("Database error occurred") from err


async def get_pending_between(
    session: AsyncSession, user_id_1: UUID, user_id_2: UUID
) -> Friendship | None:
    
    receiver_id = user_id_1
    other_user_id = user_id_2

    try:
        statement = (
            select(Friendship)
            .where(
                Friendship.user_id_1 == other_user_id,  # sender
                Friendship.user_id_2 == receiver_id,    # receiver 
                Friendship.status == "pending",
            )
            .limit(1)
        )

        result = await session.execute(statement)
        friendship = result.scalars().first()

        return friendship

    except SQLAlchemyError as err:
        raise RuntimeError("Database error occurred") from err


async def list_pending_for_user(
    session: AsyncSession, user_id: UUID
) -> list[Friendship]:
   
    try:
        statement = select(Friendship).where(
            Friendship.status == "pending",
            (Friendship.user_id_1 == user_id)
            | (Friendship.user_id_2 == user_id),
        )

        result = await session.execute(statement)
        friendships = result.scalars().all()

        return friendships

    except SQLAlchemyError as err:
        raise RuntimeError("Database error occurred") from err


async def list_incoming_for_user(
    session: AsyncSession, user_id: UUID
) -> list[Friendship]:
  
    try:
        statement = select(Friendship).where(
            Friendship.status == "pending",
            Friendship.user_id_2 == user_id,  
        )

        result = await session.execute(statement)
        friendships = result.scalars().all()

        return friendships

    except SQLAlchemyError as err:
        raise RuntimeError("Database error occurred") from err


async def list_sent_for_user(
    session: AsyncSession, user_id: UUID
) -> list[Friendship]:
  
    try:
        statement = select(Friendship).where(
            Friendship.status == "pending",
            Friendship.user_id_1 == user_id,  
        )

        result = await session.execute(statement)
        friendships = result.scalars().all()

        return friendships

    except SQLAlchemyError as err:
        raise RuntimeError("Database error occurred") from err


async def accept_request(
    session: AsyncSession, friendship: Friendship
) -> Friendship:
   
    try:
        friendship.status = "accepted"
        friendship.accepted_at = datetime.now(timezone.utc)
        session.add(friendship)

        await session.flush()
        await session.refresh(friendship)

        return friendship

    except SQLAlchemyError as err:
        raise RuntimeError("Database error occurred") from err


async def delete_request(
    session: AsyncSession, friendship: Friendship
) -> None:
    
    try:
        await session.delete(friendship)
        await session.flush()

    except SQLAlchemyError as err:
        raise RuntimeError("Database error occurred") from err

async def list_friends_for_user(
    session: AsyncSession, user_id: UUID
) -> list[User]:
   
    try:
        friendship_stmt = select(Friendship).where(
            Friendship.status == "accepted",
            or_(
                Friendship.user_id_1 == user_id,
                Friendship.user_id_2 == user_id,
            ),
        )

        result = await session.execute(friendship_stmt)
        friendships: list[Friendship] = result.scalars().all()

        if not friendships:
            return []

        friend_ids: set[UUID] = set()
        for fr in friendships:
            if fr.user_id_1 == user_id:
                friend_ids.add(fr.user_id_2)
            else:
                friend_ids.add(fr.user_id_1)

        if not friend_ids:
            return []

        users_stmt = select(User).where(User.user_id.in_(friend_ids))
        users_result = await session.execute(users_stmt)
        users = users_result.scalars().all()

        return users

    except SQLAlchemyError as err:
        raise RuntimeError("Database error occurred") from err




async def send_friend_request(
    db: AsyncSession, current_user_id: UUID, target_user_id: UUID
):
   
    if current_user_id == target_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot send a friend request to yourself.",
        )

    existing = await get_friendship(db, current_user_id, target_user_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A relationship with status "
            f"'{existing.status}' already exists.",
        )

    friendship = await create_friend_request(
        db, current_user_id, target_user_id
    )
    return friendship


async def is_friend(user_a: UUID, user_b: UUID) -> bool:
   
    async with SessionLocal() as session:
        try:
            async with session.begin():
                friendship = await get_friendship(session, user_a, user_b)

                return (
                    friendship is not None and friendship.status == "accepted"
                )

        except SQLAlchemyError as err:
            raise RuntimeError("Database error occurred") from err
