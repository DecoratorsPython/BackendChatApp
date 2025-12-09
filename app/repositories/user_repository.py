from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    """
    Return a user by email, or None if not found.
    """
    try:
        statement = select(User).where(User.email == email).limit(1)
        result = await session.execute(statement)
        user = result.scalars().first()

        return user

    except SQLAlchemyError as err:
        raise RuntimeError("Database error occurred") from err


async def get_user_by_token(
    session: AsyncSession, token_data: str
) -> User | None:
    try:
        statement = select(User).where(User.user_id == token_data.sub).limit(1)
        result = await session.execute(statement)
        user = result.scalars().first()

        return user

    except SQLAlchemyError as err:
        raise RuntimeError("Database error occurred") from err
