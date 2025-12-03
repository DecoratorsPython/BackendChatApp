# Environment variables configuration
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # For Google OAuth
    google_client_id: str
    google_client_secret: str
    google_redirect_url: str
    session_secret_key: str
    DATABASE_URL: str
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_ttl_seconds: int = 600

    class Config:
        env_file = ".env"


@lru_cache
def get_settings():
    return Settings()


settings = get_settings()

