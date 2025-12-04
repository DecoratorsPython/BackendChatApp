# # Authentication endpoints
from fastapi import APIRouter, Request, Depends, HTTPException
from starlette.responses import JSONResponse
from authlib.integrations.starlette_client import OAuthError
from sqlalchemy.orm import Session

from app.auth.oauth import oauth, fetch_google_userinfo
from app.services.auth_service import AuthService
from app.db.deps import get_db
from app.auth.tokens import RefreshRequest
from app.core.security import create_access_token
from app.auth.tokens import (
    verify_refresh_token,
    rotate_refresh_token,
    InvalidRefreshTokenError,
    ExpiredRefreshTokenError,
    RevokedRefreshTokenError,
)

router = APIRouter(tags=["auth"])


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
async def google_callback(request: Request, db: Session = Depends(get_db)):
    # exchange code -> tokens + userinfo
    try:
        userinfo = await fetch_google_userinfo(request)
    except OAuthError as error:
        raise HTTPException(
            status_code=400,
            detail=f"Google OAuth error: {error}"
        ) from error

    auth_service = AuthService(db)
    try:
        user = auth_service.upsert_user_from_google_profile(userinfo)
    except Exception as err:
        raise HTTPException(
            status_code=500,
            detail=f"User upsert error: {err}"
        ) from err

    try:
        tokens = auth_service.issue_tokens_for_user(user)
    except Exception as err:
        raise HTTPException(
            status_code=500,
            detail=f"Token issuance error: {err}"
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
def refresh(body: RefreshRequest, db: Session = Depends(get_db)):
    try:
        data = verify_refresh_token(db, body.refresh_token)
    except ExpiredRefreshTokenError as err:
        raise HTTPException(
            status_code=401,
            detail="Refresh token expired"
        ) from err
    except (InvalidRefreshTokenError, RevokedRefreshTokenError) as err:
        raise HTTPException(
            status_code=401,
            detail="Invalid refresh token"
        ) from err

    new_refresh = rotate_refresh_token(db, body.refresh_token)

    new_access = create_access_token(data.user_id)

    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "bearer",
    }

