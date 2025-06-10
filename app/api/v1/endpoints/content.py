from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from uuid import UUID
from app.api.v1.dependencies import db_session, current_user
from app.models.content import ContentItem, ContentCreate
from app.models.user import User
from app.models.product import Product
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/content", tags=["Content"])

@router.post("/", response_model=ContentItem, status_code=status.HTTP_201_CREATED)
async def save_content(data: ContentCreate, session: AsyncSession = Depends(db_session), current: User = Depends(current_user)):
    product = await session.get(Product, data.product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {data.product_id} not found."
        )
    if product.user_id != current.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have access to this product."
        )
    item = ContentItem.model_validate(data, update={"user_id": current.id})
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item

@router.get("/", response_model=list[ContentItem])
async def list_content(session: AsyncSession = Depends(db_session), current: User = Depends(current_user)):
    result = await session.execute(select(ContentItem).where(ContentItem.user_id == current.id))
    return result.scalars().all()

@router.get("/{cid}", response_model=ContentItem)
async def get_content(cid: UUID, session: AsyncSession = Depends(db_session), current: User = Depends(current_user)):
    item = await session.get(ContentItem, cid)
    if not item or item.user_id != current.id:
        raise HTTPException(404, "Content not found")
    return item

@router.put("/{cid}", response_model=ContentItem)
async def update_content(
    cid: UUID,
    data: ContentCreate,
    session: AsyncSession = Depends(db_session),
    current: User = Depends(current_user),
):
    item = await session.get(ContentItem, cid)
    if not item or item.user_id != current.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found")
    update_data = data.model_dump(exclude_unset=True)
    if "product_id" in update_data:
        product = await session.get(Product, update_data["product_id"])
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with id {update_data['product_id']} not found."
            )
        if product.user_id != current.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not have access to this product."
            )
    for key, value in update_data.items():
        setattr(item, key, value)
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item

@router.delete("/{cid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_content(cid: UUID, session: AsyncSession = Depends(db_session), current: User = Depends(current_user)):
    item = await session.get(ContentItem, cid)
    if not item or item.user_id != current.id:
        raise HTTPException(404, "Content not found")
    await session.delete(item)
    await session.commit()
    return None
