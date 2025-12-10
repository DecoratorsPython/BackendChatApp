# Manage refresh tokens (create, rotate, revoke)
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    ExpiredRefreshTokenError,
    InvalidRefreshTokenError,
    RevokedRefreshTokenError,
)
from app.db.models.user import RefreshToken
from app.schemas.refresh_token_data import RefreshTokenData


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _default_expiry() -> datetime:
    return _now_utc() + timedelta(days=settings.refresh_token_ttl_days)


async def create_refresh_token(db: AsyncSession, user_id: str) -> str:
    token_str = str(uuid4())

    rt = RefreshToken(
        token=token_str,
        user_id=user_id,
        created_at=_now_utc(),
        expires_at=_default_expiry(),
        revoked_at=None,
        rotated_from=None,
    )

    try:
        db.add(rt)
        await db.flush()
    except Exception as err:
        raise RuntimeError(f"Failed to create refresh token: {err}") from err

    return token_str


async def verify_refresh_token(
    db: AsyncSession, token_str: str
) -> RefreshTokenData:
    try:
        statement = select(RefreshToken).where(RefreshToken.token == token_str)
        result = await db.execute(statement)
        rt: RefreshToken | None = result.scalar_one_or_none()
    except Exception as err:
        raise RuntimeError(
            f"Database error during refresh token lookup: {err}"
        ) from err

    if not rt:
        raise InvalidRefreshTokenError("Unknown refresh token")

    if rt.revoked_at is not None:
        raise RevokedRefreshTokenError(
            "Refresh token has been revoked or rotated"
        )

    now = _now_utc()
    if rt.expires_at <= now:
        raise ExpiredRefreshTokenError("Refresh token has expired")

    return RefreshTokenData(
        token_id=str(rt.token_id),
        user_id=str(rt.user_id),
        expires_at=rt.expires_at,
        revoked=rt.revoked_at is not None,
    )


async def rotate_refresh_token(db: AsyncSession, old_token_str: str) -> str:
    try:
        statement = select(RefreshToken).where(
            RefreshToken.token == old_token_str
        )
        result = await db.execute(statement)
        rt: RefreshToken | None = result.scalar_one_or_none()
    except Exception as err:
        raise RuntimeError(
            f"Database error during refresh token lookup: {err}"
        ) from err

    if not rt:
        raise InvalidRefreshTokenError("Unknown refresh token")

    now = _now_utc()

    if rt.revoked_at is not None:
        raise RevokedRefreshTokenError(
            "Refresh token has already been revoked or rotated"
        )

    if rt.expires_at <= now:
        raise ExpiredRefreshTokenError("Refresh token has expired")

    rt.revoked_at = now
    db.add(rt)

    new_token_str = str(uuid4())
    new_rt = RefreshToken(
        token=new_token_str,
        user_id=rt.user_id,
        created_at=now,
        expires_at=_default_expiry(),
        revoked_at=None,
        rotated_from=rt.token_id,
    )

    try:
        db.add(new_rt)
        await db.flush()
    except Exception as err:
        raise RuntimeError(f"Failed to rotate refresh token: {err}") from err

    return new_token_str


async def revoke_refresh_token(db: AsyncSession, token_str: str) -> None:
    try:
        statement = select(RefreshToken).where(RefreshToken.token == token_str)
        result = await db.execute(statement)
        rt: RefreshToken | None = result.scalar_one_or_none()
    except Exception as err:
        raise RuntimeError(
            f"Database error during refresh token lookup: {err}"
        ) from err

    if not rt:
        return

    if rt.revoked_at is None:
        try:
            rt.revoked_at = _now_utc()
            db.add(rt)
            await db.flush()
        except Exception as err:
            raise RuntimeError(
                f"Failed to revoke refresh token: {err}"
            ) from err


async def revoke_all_for_user(db: AsyncSession, user_id: str) -> int:
    now = _now_utc()

    try:
        statement = select(RefreshToken).where(
            RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None)
        )
        result = await db.execute(statement)
        tokens = result.scalars().all()
    except Exception as err:
        raise RuntimeError(
            f"Database error during refresh tokens lookup: {err}"
        ) from err

    if not tokens:
        return 0

    try:
        for rt in tokens:
            rt.revoked_at = now
            db.add(rt)
        await db.flush()
    except Exception as err:
        raise RuntimeError(
            f"Failed to revoke all refresh tokens for user: {err}"
        ) from err

    return len(tokens)
