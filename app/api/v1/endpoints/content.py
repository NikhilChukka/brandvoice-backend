from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from uuid import UUID
from app.api.v1.dependencies import db_session, current_user
from app.models.content import ContentItem, ContentCreate
from app.models.user import User

router = APIRouter(prefix="/content", tags=["Content"])

@router.post("/", response_model=ContentItem, status_code=status.HTTP_201_CREATED)
def save_content(data: ContentCreate, session: Session = db_session(), current: User = Depends(current_user)):
    item = ContentItem.model_validate(data, update={"user_id": current.id})
    session.add(item)
    session.commit()
    session.refresh(item)
    return item

@router.get("/", response_model=list[ContentItem])
def list_content(session: Session = db_session(), current: User = Depends(current_user)):
    return session.exec(select(ContentItem).where(ContentItem.user_id == current.id)).all()

@router.get("/{cid}", response_model=ContentItem)
def get_content(cid: UUID, session: Session = db_session(), current: User = Depends(current_user)):
    item = session.get(ContentItem, cid)
    if not item or item.user_id != current.id:
        raise HTTPException(404, "Content not found")
    return item

@router.put("/{cid}", response_model=ContentItem)
def update_content(cid: UUID, data: ContentCreate, session: Session = db_session(), current: User = Depends(current_user)):
    item = session.get(ContentItem, cid)
    if not item or item.user_id != current.id:
        raise HTTPException(404, "Content not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item

@router.delete("/{cid}", status_code=status.HTTP_204_NO_CONTENT)
def delete_content(cid: UUID, session: Session = db_session(), current: User = Depends(current_user)):
    item = session.get(ContentItem, cid)
    if not item or item.user_id != current.id:
        raise HTTPException(404, "Content not found")
    session.delete(item)
    session.commit()
    return None
