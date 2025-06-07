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


from app.models.user import User
from fastapi import Depends, HTTPException, status # Added HTTPException, status
from fastapi.security import OAuth2PasswordBearer # Added OAuth2PasswordBearer
from uuid import UUID # Added UUID
from app.core.db import get_session # Added to resolve get_session dependency for get_current_user
from sqlmodel import Session # Added import for Session type hint

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login") # Added for get_current_user

# Moved from app.api.v1.endpoints.auth.py
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_session) # Assumes get_session is available or imported
) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: UUID = UUID(payload.get("sub"))
    except (JWTError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

def get_current_active_user(user: User = Depends(get_current_user)) -> User:
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return user