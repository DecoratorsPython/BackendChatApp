# Authentication services:
# - upsert user (creates and updates the user);
# - issue tokens
# - refresh access

from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.db.models.user import User
from app.core.security import create_access_token


def normalize_email(email: str | None) -> str | None:
    if not email:
        return None
    return email.strip().lower()


class AuthService:
    def __init__(self, db: Session):
        self.db = db


    def upsert_user_from_google_profile(self, profile: dict) -> User:
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
            user = (
                self.db.query(User)
                .filter(User.provider == provider, User.provider_sub == provider_sub)
                .one_or_none()
            )
        except SQLAlchemyError as db_err:
            raise Exception("Database error during user lookup") from db_err

        if not user and email:
            try:
                user = self.db.query(User).filter(User.email == email).one_or_none()
            except SQLAlchemyError as db_err:

                raise Exception("Database error during email lookup") from db_err

        if user:
            changed = False
            try:
                if username and user.username != username:
                    user.username = username
                    changed = True
                if avatar_url and user.avatar_url != avatar_url:
                    user.avatar_url = avatar_url
                    changed = True
                if user.provider != provider or user.provider_sub != provider_sub:
                    user.provider = provider
                    user.provider_sub = provider_sub
                    changed = True
                user.last_login = datetime.utcnow()
                changed = True
                if changed:
                    self.db.add(user)
                    self.db.commit()
                    self.db.refresh(user)
            except SQLAlchemyError as db_err:
                self.db.rollback()
                raise Exception("Database error during user update") from db_err
        else:
            try:
                user = User(
                    username=username,
                    email=email,
                    avatar_url=avatar_url,
                    provider=provider,
                    provider_sub=provider_sub,
                    created_at=datetime.utcnow(),
                    last_login=datetime.utcnow(),
                )
                self.db.add(user)
                self.db.commit()
                self.db.refresh(user)
            except SQLAlchemyError as db_err:
                self.db.rollback()
                raise Exception("Database error during user creation") from db_err

        return user


    def issue_access_token_for_user(self, user: User) -> str:
        if not user or not getattr(user, "user_id", None):
            raise ValueError("User object missing user_id")
        try:
            return create_access_token(str(user.user_id))
        except Exception as err:
            raise Exception("Error issuing access token") from err
