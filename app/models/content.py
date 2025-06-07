from sqlmodel import SQLModel, Field
from uuid import UUID, uuid4
from datetime import datetime

class ContentItem(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    product_id: UUID                   # FK to Product
    body_text: str
    image_url: str | None = None
    state: str = "draft"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ContentCreate(SQLModel):
    product_id: UUID
    body_text: str
    image_url: str | None = None
