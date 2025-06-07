from enum import Enum as PyEnum # Use a different alias if 'Enum' is ambiguous
from sqlmodel import SQLModel, Field
from typing import Optional # Make sure Optional is imported if used
from uuid import UUID, uuid4
from datetime import datetime
from typing import Literal

# Example Enum definition
class ScheduleStatus(str, PyEnum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"

class Schedule(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    content_id: UUID                           # FK to ContentItem
    run_at: datetime
    platform: Literal["instagram","linkedin","x"]
    state: Literal["scheduled","completed","cancelled"] = "scheduled"

class ScheduleCreate(SQLModel):
    content_id: UUID
    run_at: datetime
    platform: str
