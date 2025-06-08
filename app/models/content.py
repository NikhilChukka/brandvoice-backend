from sqlmodel import SQLModel, Field
from uuid import UUID, uuid4
from datetime import datetime

class ContentItem(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id") # Added user_id
    product_id: UUID = Field(foreign_key="product.id")                  # FK to Product
    body_text: str
    image_url: str | None = None
    state: str = "draft"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    modified_at: datetime = Field(default_factory=datetime.utcnow, nullable=True)

class ContentCreate(SQLModel):
    product_id: UUID
    body_text: str
    image_url: str | None = None
