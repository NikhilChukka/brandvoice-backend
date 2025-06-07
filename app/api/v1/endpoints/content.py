from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from uuid import UUID
from app.api.v1.dependencies import db_session
from app.models.content import ContentItem, ContentCreate

router = APIRouter(prefix="/content", tags=["Content"])

@router.post("/", response_model=ContentItem, status_code=status.HTTP_201_CREATED)
def save_content(data: ContentCreate, session: Session = db_session()):
    item = ContentItem.model_validate(data)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item

@router.get("/", response_model=list[ContentItem])
def list_content(session: Session = db_session()):
    return session.exec(select(ContentItem)).all()

@router.get("/{cid}", response_model=ContentItem)
def get_content(cid: UUID, session: Session = db_session()):
    item = session.get(ContentItem, cid)
    if not item:
        raise HTTPException(404, "Content not found")
    return item

@router.put("/{cid}", response_model=ContentItem)
def update_content(cid: UUID, data: ContentCreate, session: Session = db_session()):
    item = session.get(ContentItem, cid)
    if not item:
        raise HTTPException(404, "Content not found")
    for key, value in data.model_dump().items():
        setattr(item, key, value)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item

@router.delete("/{cid}", status_code=status.HTTP_204_NO_CONTENT)
def delete_content(cid: UUID, session: Session = db_session()):
    item = session.get(ContentItem, cid)
    if not item:
        raise HTTPException(404, "Content not found")
    session.delete(item)
    session.commit()
    return None
