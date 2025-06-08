from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from uuid import UUID
from app.api.v1.dependencies import db_session, current_user
from app.models.product import Product, ProductCreate, ProductRead
from app.models.user import User

router = APIRouter(prefix="/products", tags=["Products"])

@router.post("/", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(data: ProductCreate, session: Session = db_session(), current: User = Depends(current_user)):
    prod = Product.model_validate(data, update={"user_id": current.id})
    session.add(prod)
    session.commit()
    session.refresh(prod)
    return prod

@router.get("/", response_model=list[ProductRead])
def list_products(session: Session = db_session(), current: User = Depends(current_user)):
    return session.exec(select(Product).where(Product.user_id == current.id)).all()

@router.get("/{pid}", response_model=ProductRead)
def get_product(pid: UUID, session: Session = db_session(), current: User = Depends(current_user)):
    prod = session.get(Product, pid)
    if not prod or prod.user_id != current.id:
        raise HTTPException(404, "Product not found")
    return prod

@router.put("/{pid}", response_model=ProductRead)
def update_product(
    pid: UUID, data: ProductCreate, session: Session = db_session(), current: User = Depends(current_user)
):
    prod = session.get(Product, pid)
    if not prod or prod.user_id != current.id:
        raise HTTPException(404, "Product not found")
    prod.name = data.name
    prod.description = data.description
    prod.price_cents = data.price_cents
    session.add(prod)
    session.commit()
    session.refresh(prod)
    return prod

@router.delete("/{pid}", status_code=204)
def delete_product(pid: UUID, session: Session = db_session(), current: User = Depends(current_user)):
    prod = session.get(Product, pid)
    if not prod or prod.user_id != current.id:
        raise HTTPException(404, "Product not found")
    session.delete(prod)
    session.commit()
