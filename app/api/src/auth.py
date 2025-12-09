# # Authentication endpoints
from authlib.integrations.starlette_client import OAuthError
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from app.auth.oauth import fetch_google_userinfo, oauth
from app.auth.tokens import (
    ExpiredRefreshTokenError,
    InvalidRefreshTokenError,
    RevokedRefreshTokenError,
    revoke_all_for_user,
    revoke_refresh_token,
    rotate_refresh_token,
    verify_refresh_token,
)
from app.core.deps import get_current_user
from app.core.security import create_access_token
from app.db.deps import get_db
from app.db.models.user import User
from app.schemas.logout_request import LogoutRequest
from app.schemas.refresh_request import RefreshRequest
from app.services.auth_service import AuthService

router = APIRouter(tags=["auth"])

get_db_dependency = Depends(get_db)
current_user_dependency = Depends(get_current_user)


# ---- Dev-only test endpoints ----


@router.get("/dev/auth/google/login", name="dev_google_login")
async def dev_google_login(request: Request):
    redirect_uri = request.url_for("dev_google_callback")
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/dev/auth/google/callback", name="dev_google_callback")
async def dev_google_callback(request: Request):
    userinfo = await fetch_google_userinfo(request)
    return userinfo


# ---- Production-style endpoints ----


@router.get("/auth/google/login", name="google_login")
async def google_login(request: Request):
    redirect_uri = request.url_for("google_callback")
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/auth/google/callback", name="google_callback")
async def google_callback(
    request: Request, db: AsyncSession = get_db_dependency
):
    # exchange code -> tokens + userinfo
    try:
        userinfo = await fetch_google_userinfo(request)
    except OAuthError as error:
        raise HTTPException(
            status_code=400, detail=f"Google OAuth error: {error}"
        ) from error

    try:
        async with db.begin():
            auth_service = AuthService(db)
            user = await auth_service.upsert_user_from_google_profile(userinfo)
            tokens = await auth_service.issue_tokens_for_user(user)

    except SQLAlchemyError as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error during auth flow",
        ) from err

    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"User/token error: {err}",
        ) from err

    return JSONResponse(
        {
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "token_type": tokens["token_type"],
            "user": {
                "user_id": str(user.user_id),
                "username": user.username,
                "email": user.email,
                "avatar_url": user.avatar_url,
                "provider": user.provider,
            },
        }
    )


@router.post("/auth/refresh")
async def refresh(body: RefreshRequest, db: AsyncSession = get_db_dependency):
    try:
        async with db.begin():
            data = await verify_refresh_token(db, body.refresh_token)
            new_refresh = await rotate_refresh_token(db, body.refresh_token)
            new_access = create_access_token(data.user_id)

    except ExpiredRefreshTokenError as err:
        raise HTTPException(
            status_code=401, detail="Refresh token expired"
        ) from err

    except (InvalidRefreshTokenError, RevokedRefreshTokenError) as err:
        raise HTTPException(
            status_code=401, detail="Invalid refresh token"
        ) from err

    except SQLAlchemyError as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error",
        ) from err

    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token rotation error: {err}",
        ) from err

    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "bearer",
    }


@router.post("/auth/logout")
async def logout(
    body: LogoutRequest,
    current_user: User = current_user_dependency,
    db: AsyncSession = get_db_dependency,
):
    try:
        async with db.begin():
            await revoke_refresh_token(db, body.refresh_token)

    except SQLAlchemyError as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error during logout: {err}",
        ) from err

    except Exception as err:
        raise HTTPException(
            status_code=500, detail=f"Logout error: {err}"
        ) from err

    return {
        "detail": "Logged out from current device. "
        "Please delete tokens on client."
    }


@router.post("/auth/logout-all")
async def logout_all(
    current_user: User = current_user_dependency,
    db: AsyncSession = get_db_dependency,
):
    try:
        async with db.begin():
            count = await revoke_all_for_user(db, str(current_user.user_id))

    except SQLAlchemyError as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error during logout-all: {err}",
        ) from err

    except Exception as err:
        raise HTTPException(
            status_code=500, detail=f"Logout-all error: {err}"
        ) from err

    return {
        "detail": f"Logged out from {count} sessions (all devices). "
        "Please delete tokens on client."
    }
