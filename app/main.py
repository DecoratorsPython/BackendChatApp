# FastAPI application setup
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
from app.api.src.auth import router as auth_router
from app.api.src.users import router as users_router
from app.core.config import settings
from app.api.src import friendships



app = FastAPI()

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SessionMiddleware, secret_key=settings.session_secret_key)

app.include_router(auth_router)
app.include_router(users_router)

app.include_router(friendships.router)

