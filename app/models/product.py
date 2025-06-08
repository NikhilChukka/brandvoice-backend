from sqlmodel import SQLModel, Field
from uuid import UUID, uuid4
from typing import Optional
from datetime import datetime

class Product(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id") # Added user_id
    name: str
    description: Optional[str] = None
    price_cents: int
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    modified_at: Optional[datetime] = Field(default_factory=datetime.utcnow, nullable=True)

# ----- DTOs -----
class ProductCreate(SQLModel):
    name: str
    user_id: UUID  # Added user_id
    description: Optional[str] = None
    price_cents: int

class ProductRead(SQLModel):
    id: UUID
    user_id: UUID # Added user_id
    name: str
    description: Optional[str] = None
    price_cents: int
