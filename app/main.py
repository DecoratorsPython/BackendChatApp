# FastAPI application setup
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from app.api.src.auth import router as auth_router
from app.api.src.users import router as users_router
from app.core.config import settings
from app.ws.chat import router as ws_router
from app.api.src import friendships



app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key=settings.session_secret_key)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(ws_router)

app.include_router(friendships.router)

