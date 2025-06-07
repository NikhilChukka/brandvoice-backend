from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer 
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select
from uuid import UUID
from ..dependencies import get_session  # your DB dep
from app.core.security import (
    verify_password, get_password_hash,
    create_access_token, create_refresh_token,
    Token
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
def register(data: UserCreate, db: Session = Depends(get_session)):
    user = User(
        email=data.email.lower(),
        full_name=data.full_name,
        hashed_password=get_password_hash(data.password)
    )
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Email already registered")
    return user

# ───────────────────────── login
@router.post("/login", response_model=Token)
def login(
    form: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_session)
):
    stmt = select(User).where(User.email == form.username.lower())
    user = db.exec(stmt).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect credentials")
    access = create_access_token(str(user.id))
    refresh = create_refresh_token(str(user.id))
    return Token(access_token=access, refresh_token=refresh)

# ───────────────────────── refresh
@router.post("/refresh", response_model=Token)
def refresh(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    new_access = create_access_token(payload["sub"])
    new_refresh = create_refresh_token(payload["sub"])
    return Token(access_token=new_access, refresh_token=new_refresh)

# ───────────────────────── helpers to protect routes
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_session)
) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: UUID = UUID(payload.get("sub"))
    except (JWTError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

def get_current_active_user(user: User = Depends(get_current_user)) -> User:
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user

# ───────────────────────── who-am-I
@router.get("/me", response_model=UserRead)
def me(current: User = Depends(get_current_active_user)):
    return current

# ───────────────────────── sample protected
@router.get("/demo-protected")
def protected_route(current: User = Depends(get_current_active_user)):
    return {"message": f"Hello {current.full_name or current.email}!"}


@router.get("/user/{user_id}", response_model=UserRead, summary="Get a user’s public profile")
def get_user_details(
    user_id: UUID,
    current: User = Depends(get_current_active_user),   # <- your JWT guard
    db: Session = Depends(get_session),                 # <- DB session
):
    """
    Fetch a single user's profile.

    • Ordinary users may call this on **their own** ID  
    • Admin users (`is_admin=True`) may fetch anyone
    """
    # ---- optional ACL check --------------------------------------------
    if user_id != current.id and not getattr(current, "is_admin", False):
        raise HTTPException(status_code=403, detail="Not authorised")

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user