from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordRequestForm
from app.models.user import User, UserCreate, UserInDB, UserUpdate
from app.services.user_service import UserService
from app.api.v1.dependencies import get_firebase_user
from app.models.firestore_db import (
    create_firebase_user,
    verify_firebase_token,
    get_firebase_user as get_firestore_user,
    sign_in_with_email_password
)
from app.core.db_dependencies import db_session
from typing import Dict
from firebase_admin import auth as firebase_auth
import httpx
import os

router = APIRouter(tags=["Authentication"])

security = HTTPBearer()

@router.post("/register", response_model=Dict[str, str])
async def register(
    user_in: UserCreate,
):
    """
    Register a new user with Firebase Authentication.
    """
    # Registration logic should use Firebase only, or you can remove this endpoint if not needed
    raise HTTPException(status_code=501, detail="Registration via API not implemented. Use Firebase Auth client SDK.")

@router.post("/login", response_model=Dict[str, str])
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    """
    Login with Firebase Authentication using email and password.
    Returns Firebase ID token and refresh token on success.
    """
    FIREBASE_API_KEY = os.getenv("FIREBASE_WEB_API_KEY")
    if not FIREBASE_API_KEY:
        raise HTTPException(status_code=500, detail="FIREBASE_WEB_API_KEY environment variable is not set")
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
    payload = {
        "email": form_data.username,
        "password": form_data.password,
        "returnSecureToken": True
    }
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload)
            if resp.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid email or password")
            data = resp.json()
        return {
            "access_token": data["idToken"],
            "refresh_token": data["refreshToken"],
            "token_type": "bearer",
            "user_id": data["localId"]
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Login failed: {str(e)}")

@router.get("/me", response_model=User)
async def get_current_user_info(
    current_user: User = Depends(get_firebase_user)
):
    """
    Get current user information.
    """
    return current_user

@router.put("/me", response_model=User)
async def update_current_user_info(
    user_update: UserUpdate,
    current_user: User = Depends(get_firebase_user),
):
    """
    Update current user information. Email cannot be updated.
    """
    # Updating user info in Firebase Auth is not implemented here
    raise HTTPException(status_code=501, detail="User update not implemented. Use Firebase Auth client SDK.")

@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_current_user(
    current_user: User = Depends(get_firebase_user),
):
    """
    Delete current user account.
    """
    # Deleting user in Firebase Auth is not implemented here
    raise HTTPException(status_code=501, detail="User deletion not implemented. Use Firebase Auth client SDK.")