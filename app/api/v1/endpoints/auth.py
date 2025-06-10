from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer 
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from uuid import UUID
from ..dependencies import db_session, current_user  # Use db_session, not get_session
from app.core.security import (
    verify_password, get_password_hash,
    create_access_token, create_refresh_token,
    Token,
    get_current_active_user  # Added direct import for clarity in this file if preferred
)
from app.models.user import User, UserCreate, UserRead
from jose import jwt, JWTError
from app.core.config import get_settings

_settings = get_settings()
SECRET_KEY = _settings.secret_key
ALGORITHM = _settings.algorithm


router = APIRouter(prefix="/auth", tags=["Auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login") 

# ───────────────────────── register
@router.post("/register", response_model=UserRead, status_code=201)
async def register(data: UserCreate, db: AsyncSession = Depends(db_session)):
    user = User(
        email=data.email.lower(),
        full_name=data.full_name,
        hashed_password=get_password_hash(data.password)
    )
    db.add(user)
    try:
        await db.commit()
        await db.refresh(user)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Email already registered")
    return user

# ───────────────────────── login
@router.post("/login", response_model=Token)
async def login(
    form: OAuth2PasswordRequestForm = Depends(), 
    db: AsyncSession = Depends(db_session)
):
    stmt = select(User).where(User.email == form.username.lower())
    result = await db.execute(stmt)
    user = result.scalars().first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect credentials")
    access = create_access_token(str(user.id))
    refresh = create_refresh_token(str(user.id))
    return Token(access_token=access, refresh_token=refresh)

# ───────────────────────── refresh
@router.post("/refresh", response_model=Token)
async def refresh(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    new_access = create_access_token(payload["sub"])
    new_refresh = create_refresh_token(payload["sub"])
    return Token(access_token=new_access, refresh_token=new_refresh)

# ───────────────────────── who-am-I
@router.get("/me", response_model=UserRead)
async def me(current: User = Depends(current_user)):
    return current

# ───────────────────────── sample protected
@router.get("/demo-protected")
async def protected_route(current: User = Depends(current_user)):
    return {"message": f"Hello {current.full_name or current.email}!"}


@router.get("/user/{user_id}", response_model=UserRead, summary="Get a user’s public profile")
async def get_user_details(
    user_id: UUID,
    current: User = Depends(current_user),   # <- Use current_user from dependencies
    db: AsyncSession = Depends(db_session),                 # <- DB session
):
    """
    Fetch a single user's profile.

    • Ordinary users may call this on **their own** ID  
    • Admin users (`is_admin=True`) may fetch anyone
    """
    # ---- optional ACL check --------------------------------------------
    if user_id != current.id and not getattr(current, "is_admin", False):
        raise HTTPException(status_code=403, detail="Not authorised")

    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user