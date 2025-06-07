from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
from dotenv import load_dotenv
import os

# Load the .env file from the 'app' directory
# Adjust the path if your .env file is located elsewhere relative to this config.py
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env') # Assumes .env is in the parent 'app' directory
load_dotenv(dotenv_path=dotenv_path)

class Settings(BaseSettings):
    # ----- app -----
    app_name: str = "BrandVoice API"
    environment: str = "dev"

    # ----- db -----
    database_url: str = os.getenv("DATABASE_URL")

    # ----- auth / jwt -----
    secret_key: str = os.getenv("SECRET_KEY")
    algorithm: str = os.getenv("ALGORITHM")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
    refresh_token_expire_days: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))

    # ----- CORS -----
    allow_origins: List[str] = [origin.strip() for origin in os.getenv("ALLOW_ORIGINS", "").split(',')]

    # ----- misc (optional) -----
    redis_url: str | None = None
    broker_url: str | None = None
    result_backend: str | None = None

    # read from .env by default
    model_config = SettingsConfigDict(
        env_file="app/.env",
    )

@lru_cache
def get_settings() -> Settings:
    """
    Import-safe singleton – FastAPI can `Depends(get_settings)`.
    Caches so the same object is reused across requests.
    """
    return Settings()
