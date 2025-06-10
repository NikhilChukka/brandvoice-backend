# app/models/scheduling.py
from datetime import datetime
from sqlmodel import SQLModel, Field

class ScheduledPost(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: str
    text: str
    media_paths: str | None = None   # JSON‐encoded list of paths, or null
    run_at: datetime
    status: str = Field(default="pending", index=True)
