# app/api/v1/endpoints/schedule.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from uuid import UUID
from app.api.v1.dependencies import db_session, current_user
from app.models.schedule import Schedule, ScheduleCreate, ScheduleUpdate
from app.models.user import User
from app.models.content import ContentItem
from fastapi import Response
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Form, File, UploadFile
from datetime import datetime
import json
import uuid
from app.models.user import User
from app.models.scheduling import ScheduledPost
from starlette.status import HTTP_201_CREATED
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/users/{user_id}/schedules", tags=["Scheduler"])

# ───────────────────────── helpers
async def _own_or_404(session: AsyncSession, sid: UUID, user_id: UUID) -> Schedule:
    sched = await session.get(Schedule, sid)
    if not sched or sched.user_id != user_id:
        raise HTTPException(404, "Schedule not found")
    return sched

# ───────────────────────── CRUD
@router.get("/", response_model=dict)
async def list_schedules(
    user_id: UUID,
    session: AsyncSession = Depends(db_session),
    current: User = Depends(current_user)
) -> dict[str, Any]:
    if user_id != current.id:
        raise HTTPException(403, "Not allowed to access this user's schedules")
    stmt = select(Schedule).where(Schedule.user_id == user_id)
    result = await session.execute(stmt)
    schedules = result.scalars().all()
    return {"count": len(schedules), "results": schedules}

@router.post("/", response_model=Schedule, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    user_id: UUID,
    data: ScheduleCreate,
    session: AsyncSession = Depends(db_session),
    current: User = Depends(current_user)
):
    if user_id != current.id:
        raise HTTPException(403, "Not allowed to access this user's schedules")
    if not await session.get(ContentItem, data.content_id):
        raise HTTPException(404, "Content item not found")
    sched = Schedule.model_validate(data, update={"user_id": user_id})
    session.add(sched)
    await session.commit()
    await session.refresh(sched)
    # TODO: enqueue APScheduler/Celery job here
    return sched

@router.get("/{sid}", response_model=Schedule)
async def get_schedule(
    user_id: UUID, sid: UUID,
    session: AsyncSession = Depends(db_session),
    current: User = Depends(current_user)
):
    if user_id != current.id:
        raise HTTPException(403, "Not allowed to access this user's schedules")
    return await _own_or_404(session, sid, user_id)

@router.put("/{sid}", response_model=Schedule)
async def update_schedule(
    user_id: UUID, sid: UUID,
    data: ScheduleUpdate,
    session: AsyncSession = Depends(db_session),
    current: User = Depends(current_user)
):
    if user_id != current.id:
        raise HTTPException(403, "Not allowed to access this user's schedules")
    sched = await _own_or_404(session, sid, user_id)
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(sched, k, v)
    session.add(sched)
    await session.commit()
    await session.refresh(sched)
    return sched

@router.delete("/{sid}", status_code=204)
async def delete_schedule(
    user_id: UUID, sid: UUID,
    session: AsyncSession = Depends(db_session),
    current: User = Depends(current_user)
):
    if user_id != current.id:
        raise HTTPException(403, "Forbidden")
    sched = await _own_or_404(session, sid, user_id)
    await session.delete(sched)
    await session.commit()

@router.post("/schedule", status_code=HTTP_201_CREATED)
async def schedule_tweet(
    text: str = Form(...),
    run_at: datetime = Form(...),  # ISO8601 datetime string
    media: list[UploadFile] | None = File(None),
    session: AsyncSession = Depends(db_session),
    user = Depends(current_user)
):
    paths = []
    if media:
        for file in media:
            filename = f"/tmp/{uuid.uuid4().hex}_{file.filename}"
            with open(filename, "wb") as f:
                f.write(file.file.read())
            paths.append(filename)
    post = ScheduledPost(
        user_id=user.id,
        text=text,
        media_paths=json.dumps(paths) if paths else None,
        run_at=run_at,
    )
    session.add(post)
    await session.commit()
    await session.refresh(post)
    from app.main import scheduler, dispatch_scheduled_tweet
    scheduler.add_job(
        func=dispatch_scheduled_tweet,
        trigger="date",
        run_date=run_at,
        args=[post.id],
        id=str(post.id),
    )
    return {"status": "scheduled", "post_id": post.id}