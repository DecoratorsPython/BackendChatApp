# Everything specific to Google/Facebook OAuth,
# including the returning of a profile for the service layer

from authlib.integrations.starlette_client import OAuth, OAuthError
from fastapi import HTTPException, Request
from app.core.config import settings


oauth = OAuth()


oauth.register(
    name="google",
    client_id=settings.google_client_id,
    client_secret=settings.google_client_secret,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={
        "scope": "openid email profile",
    },
)


async def build_google_authorize_redirect(request: Request) -> object:
    redirect_uri = request.url_for("google_callback")
    return await oauth.google.authorize_redirect(request, redirect_uri)


async def fetch_google_userinfo(request: Request) -> dict:
    try:
        token = await oauth.google.authorize_access_token(request)
    except OAuthError as error:
        raise HTTPException(
            status_code=400,
            detail=f"Google OAuth error: {error}"
        ) from error

    userinfo = token.get("userinfo")
    if not userinfo:
        raise HTTPException(status_code=400, detail="No 'userinfo' in Google OAuth response")

    return userinfo
