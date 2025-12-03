# app/core/security.py
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from pydantic import BaseModel, ValidationError

from app.core.config import settings


class TokenData(BaseModel):
    sub: str   # user_id
    iat: int   # issued at
    exp: int   # expiry


class InvalidTokenError(Exception):
    """Raised when a token is invalid or cannot be decoded."""
    pass


class ExpiredTokenError(Exception):
    """Raised when a token is valid but expired."""
    pass


def create_access_token(user_id: str) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(seconds=settings.access_token_ttl_seconds)

    payload: dict[str, Any] = {
        "sub": user_id,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }

    token = jwt.encode(
        payload,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )

    return token


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except jwt.ExpiredSignatureError as exc:
        raise ExpiredTokenError("Access token has expired") from exc
    except (jwt.InvalidTokenError, Exception) as exc:
        raise InvalidTokenError(f"Invalid access token: {exc}") from exc


def verify_access_token(token: str) -> TokenData:
    payload = decode_access_token(token)

    try:
        return TokenData(**payload)
    except ValidationError as ve:
        raise InvalidTokenError(
            f"Token payload has invalid structure: {ve}"
        ) from ve
