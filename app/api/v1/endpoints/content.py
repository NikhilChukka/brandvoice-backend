from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from uuid import UUID
from api.v1.dependencies import db_session
from models.content import ContentItem, ContentCreate

router = APIRouter(prefix="/content", tags=["Content"])

@router.post("/", response_model=ContentItem, status_code=status.HTTP_201_CREATED)
def save_content(data: ContentCreate, session: Session = Depends(db_session)):
    item = ContentItem.model_validate(data)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item

@router.get("/", response_model=list[ContentItem])
def list_content(session: Session = Depends(db_session)):
    return session.exec(select(ContentItem)).all()

@router.get("/{cid}", response_model=ContentItem)
def get_content(cid: UUID, session: Session = Depends(db_session)):
    item = session.get(ContentItem, cid)
    if not item:
        raise HTTPException(404, "Content not found")
    return item
