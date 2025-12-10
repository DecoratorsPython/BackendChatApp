# Dependencies used across the application
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    ExpiredTokenError,
    InvalidTokenError,
    verify_access_token,
)
from app.db.deps import get_db
from app.db.models.user import User
from app.repositories.user_repository import get_user_by_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token-not-used-here")

token_dependency = Depends(oauth2_scheme)
get_db_dependency = Depends(get_db)


async def get_current_user(
    token: str = token_dependency,
    db: AsyncSession = get_db_dependency,
) -> User:
    try:
        async with db.begin():
            try:
                token_data = verify_access_token(token)
            except ExpiredTokenError as err:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Access token has expired",
                ) from err
            except InvalidTokenError as err:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid access token",
                ) from err

            user = await get_user_by_token(db, token_data)

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found",
                )

            return user

    except SQLAlchemyError as err:
        raise RuntimeError("Database error occurred") from err
