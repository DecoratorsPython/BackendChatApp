from collections.abc import AsyncGenerator

from .session import SessionLocal


async def get_db() -> AsyncGenerator:
    async with SessionLocal() as db:
        yield db
