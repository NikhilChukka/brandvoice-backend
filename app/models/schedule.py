# app/models/schedule.py
from sqlmodel import SQLModel, Field, Column, JSON
from uuid import uuid4, UUID
from datetime import datetime
from typing import List
from app.models.enums import Platform, ScheduleState

class Schedule(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID                               # link to auth.User.id
    content_id: UUID                            # FK to ContentItem.id
    platforms: List[Platform] = Field(
        sa_column=Column(JSON)                  # stored as JSONB on Postgres
    )
    run_at: datetime
    timezone: str                               # e.g. "America/New_York"
    status: ScheduleState = ScheduleState.scheduled

# ---- DTOs ---------------------------------------------------------------
class ScheduleCreate(SQLModel):
    content_id: UUID
    platforms: List[Platform]
    run_at: datetime
    timezone: str

class ScheduleUpdate(SQLModel):
    platforms: List[Platform] | None = None
    run_at: datetime | None = None
    timezone: str | None = None
    status: ScheduleState | None = None
