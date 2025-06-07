from sqlmodel import SQLModel, Field
from uuid import UUID, uuid4
from typing import Optional

class Product(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str
    description: Optional[str] = None
    price_cents: int

# ----- DTOs -----
class ProductCreate(SQLModel):
    name: str
    description: Optional[str] = None
    price_cents: int

class ProductRead(SQLModel):
    id: UUID
    name: str
    description: Optional[str] = None
    price_cents: int
