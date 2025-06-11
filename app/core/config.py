from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
from dotenv import load_dotenv
import os

# Load the .env file from the project root (parent of 'app' directory)
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

class Settings(BaseSettings):
    # ----- app -----
    app_name: str = "BrandVoice API"
    environment: str = "dev"

    # ----- db -----
    database_url: str = os.getenv("DATABASE_URL", "")

    # ----- auth / jwt -----
    secret_key: str = os.getenv("SECRET_KEY", "")
    algorithm: str = os.getenv("ALGORITHM", "")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
    refresh_token_expire_days: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))

    # ----- CORS -----
    allow_origins: List[str] = [origin.strip() for origin in os.getenv("ALLOW_ORIGINS", "").split(',')]

    # ----- Twitter API -----
    twitter_api_key: str = os.getenv("TWITTER_API_KEY", "")
    twitter_api_secret: str = os.getenv("TWITTER_API_SECRET", "")
    twitter_callback_url: str = os.getenv("TWITTER_CALLBACK_URL", "")
    twitter_bearer_token: str = os.getenv("TWITTER_BEARER_TOKEN", "")

    # ----- misc (optional) -----
    redis_url: str | None = None
    broker_url: str | None = None
    result_backend: str | None = None

    # read from .env by default
    model_config = SettingsConfigDict(
        env_file="../.env",  # Correct path to project root .env
    )

    facebook_app_id: str = os.getenv("FACEBOOK_OA2_CLIENT_ID", "")
    facebook_app_secret: str = os.getenv("FACEBOOK_OA2_CLIENT_SECRET", "")
    facebook_callback_url: str = os.getenv("FACEBOOK_CALLBACK_URL", "")
    instagram_callback_url: str = os.getenv("INSTAGRAM_CALLBACK_URL", "")
@lru_cache
def get_settings() -> Settings:
    """
    Import-safe singleton – FastAPI can `Depends(get_settings)`.
    Caches so the same object is reused across requests.
    """
    return Settings()
