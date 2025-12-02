# Authentication endpoints
from fastapi import APIRouter, Request
from app.auth.oauth import oauth


router = APIRouter(tags=["auth"])

@router.get("/dev/auth/google/login", name="dev_google_login")
async def dev_google_login(request: Request):
    redirect_uri = request.url_for("dev_google_callback")
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/dev/auth/google/callback", name="dev_google_callback")
async def dev_google_callback(request: Request):
    token = await oauth.google.authorize_access_token(request)
    userinfo = token.get("userinfo")
    return userinfo