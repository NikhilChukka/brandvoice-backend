from sqlmodel import SQLModel, Field
from uuid import UUID, uuid4
from typing import Optional
from datetime import datetime

class User(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(index=True, unique=True)
    hashed_password: str
    full_name: Optional[str] = None
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    modified_at: datetime = Field(default_factory=datetime.utcnow)
    twitter_access_token: Optional[str] = None
    twitter_access_token_secret: Optional[str] = None
    # in app/models/user.py
    instagram_page_access_token: str | None = None
    instagram_business_account_id: str | None = None
    fb_page_id: str | None = None
    fb_page_access_token: str | None = None
    youtube_access_token : str | None = None
    youtube_channel_id: str | None = None
    youtube_refresh_token: str | None = None

# Pydantic response & request schemas
class UserCreate(SQLModel):
    email: str
    password: str
    full_name: Optional[str] = None

class UserRead(SQLModel):
    id: UUID
    email: str
    full_name: Optional[str] = None
