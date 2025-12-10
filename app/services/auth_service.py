# Authentication services:
# - upsert user (creates and updates the user);
# - issue tokens
# - refresh access
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.tokens import create_refresh_token
from app.core.security import create_access_token
from app.db.models.user import User


def normalize_email(email: str | None) -> str | None:
    if not email:
        return None
    return email.strip().lower()


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def upsert_user_from_google_profile(self, profile: dict) -> User:
        provider = "google"
        try:
            provider_sub = profile["sub"]
        except KeyError as err:
            raise ValueError("Google profile missing 'sub' field") from err

        email_raw = profile.get("email")
        email = normalize_email(email_raw)
        username = profile.get("name")
        avatar_url = profile.get("picture")

        if not username:
            raise ValueError("Google profile missing 'name' field")

        user = None
        try:
            statement = (
                select(User)
                .where(
                    User.provider == provider,
                    User.provider_sub == provider_sub,
                )
                .limit(1)
            )
            result = await self.db.execute(statement)
            user = result.scalars().one_or_none()
        except SQLAlchemyError as db_err:
            raise Exception("Database error during user lookup") from db_err

        if not user and email:
            try:
                statement = select(User).where(User.email == email).limit(1)
                result = await self.db.execute(statement)
                user = result.scalars().one_or_none()
            except SQLAlchemyError as db_err:
                raise Exception(
                    "Database error during email lookup"
                ) from db_err

        if user:
            changed = False
            try:
                if username and user.username != username:
                    user.username = username
                    changed = True
                if avatar_url and user.avatar_url != avatar_url:
                    user.avatar_url = avatar_url
                    changed = True
                if (
                    user.provider != provider
                    or user.provider_sub != provider_sub
                ):
                    user.provider = provider
                    user.provider_sub = provider_sub
                    changed = True
                user.last_login = datetime.now(timezone.utc)
                changed = True
                if changed:
                    self.db.add(user)
                    await self.db.flush()
                    await self.db.refresh(user)
            except SQLAlchemyError as db_err:
                raise Exception(
                    "Database error during user update"
                ) from db_err
        else:
            try:
                user = User(
                    username=username,
                    email=email,
                    avatar_url=avatar_url,
                    provider=provider,
                    provider_sub=provider_sub,
                    created_at=datetime.now(timezone.utc),
                    last_login=datetime.now(timezone.utc),
                )
                self.db.add(user)
                await self.db.flush()
                await self.db.refresh(user)
            except SQLAlchemyError as db_err:
                raise Exception(
                    "Database error during user creation"
                ) from db_err

        return user

    async def issue_tokens_for_user(self, user: User) -> dict:
        user_id = str(user.user_id)
        try:
            access = create_access_token(user_id)
            refresh = await create_refresh_token(self.db, user_id)
        except Exception as err:
            raise RuntimeError(
                f"Failed to issue tokens for user: {err}"
            ) from err
        return {
            "access_token": access,
            "refresh_token": refresh,
            "token_type": "bearer",
        }
