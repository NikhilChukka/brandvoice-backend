from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class TwitterCredentialBase(BaseModel):
    """Base model for Twitter credentials."""
    access_token: str = Field(..., description="Twitter Access Token")
    refresh_token: str = Field(..., description="Twitter Refresh Token")
    user_id: str = Field(..., description="User ID who owns this credential")

class TwitterCredentialCreate(TwitterCredentialBase):
    """Model for creating Twitter credentials."""
    pass

class TwitterCredentialUpdate(BaseModel):
    """Model for updating Twitter credentials."""
    access_token: Optional[str] = Field(None, description="Twitter Access Token")
    refresh_token: Optional[str] = Field(None, description="Twitter Refresh Token")

class TwitterCredential(TwitterCredentialBase):
    """Model for Twitter credentials."""
    id: str = Field(..., description="Credential ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True 