# Environment variables configuration
from pydantic_settings import BaseSettings
 
class Settings(BaseSettings):
    # For Google OAuth
    google_client_id: str
    google_client_secret: str
    google_redirect_url: str
    session_secret_key: str
    
    class Config:
        env_file = ".env"

settings = Settings()
