from passlib.context import CryptContext        # bcrypt wrapper :contentReference[oaicite:4]{index=4}
from datetime import datetime, timedelta
from typing import Any, Union
from jose import jwt, JWTError                 # jose = python-jose :contentReference[oaicite:5]{index=5}
from pydantic import BaseModel
from app.core.config import get_settings

_settings = get_settings()

# ── config ───────────────────────────
SECRET_KEY = _settings.secret_key
ALGORITHM = _settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = _settings.access_token_expire_minutes
REFRESH_TOKEN_EXPIRE_DAYS = _settings.refresh_token_expire_days
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def get_password_hash(plain: str) -> str:
    return pwd_context.hash(plain)

def _create_token(subject: Union[str, Any], expires_delta: timedelta) -> str:
    now = datetime.utcnow()
    payload = {
        "sub": str(subject),
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def create_access_token(subject: str) -> str:
    return _create_token(subject, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))

def create_refresh_token(subject: str) -> str:
    return _create_token(subject, timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
