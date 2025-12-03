# Dependencies used across the application
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import verify_access_token, InvalidTokenError, ExpiredTokenError
from app.db.deps import get_db 
from app.db.models.user import User


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token-not-used-here")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
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

    user = (
        db.query(User)
        .filter(User.user_id == token_data.sub)
        .one_or_none()
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user
