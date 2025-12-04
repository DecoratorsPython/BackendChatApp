# Environment variables configuration
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # For Google OAuth
    google_client_id: str
    google_client_secret: str
    google_redirect_url: str
    session_secret_key: str

    # Database
    DATABASE_URL: str

    # JWT / auth
    jwt_secret: str = Field(..., alias="JWT_SECRET")
    jwt_algorithm: str = Field("HS256", alias="JWT_ALGORITHM")
    access_token_ttl_seconds: int = Field(600, alias="ACCESS_TOKEN_TTL_SECONDS")

    class Config:
        env_file = ".env"
        extra = "ignore"  


settings = Settings()
