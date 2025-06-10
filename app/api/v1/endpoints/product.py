from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from uuid import UUID
from app.api.v1.dependencies import db_session, current_user
from app.models.product import Product, ProductCreate, ProductRead
from app.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/products", tags=["Products"])

@router.post("/", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
async def create_product(data: ProductCreate, session: AsyncSession = Depends(db_session), current: User = Depends(current_user)):
    prod = Product.model_validate(data, update={"user_id": current.id})
    session.add(prod)
    await session.commit()
    await session.refresh(prod)
    return prod

@router.get("/", response_model=list[ProductRead])
async def list_products(session: AsyncSession = Depends(db_session), current: User = Depends(current_user)):
    result = await session.execute(select(Product).where(Product.user_id == current.id))
    return result.scalars().all()

@router.get("/{pid}", response_model=ProductRead)
async def get_product(pid: UUID, session: AsyncSession = Depends(db_session), current: User = Depends(current_user)):
    prod = await session.get(Product, pid)
    if not prod or prod.user_id != current.id:
        raise HTTPException(404, "Product not found")
    return prod

@router.put("/{pid}", response_model=ProductRead)
async def update_product(
    pid: UUID, data: ProductCreate, session: AsyncSession = Depends(db_session), current: User = Depends(current_user)
):
    prod = await session.get(Product, pid)
    if not prod or prod.user_id != current.id:
        raise HTTPException(404, "Product not found")
    prod.name = data.name
    prod.description = data.description
    prod.price_cents = data.price_cents
    session.add(prod)
    await session.commit()
    await session.refresh(prod)
    return prod

@router.delete("/{pid}", status_code=204)
async def delete_product(pid: UUID, session: AsyncSession = Depends(db_session), current: User = Depends(current_user)):
    prod = await session.get(Product, pid)
    if not prod or prod.user_id != current.id:
        raise HTTPException(404, "Product not found")
    await session.delete(prod)
    await session.commit()
