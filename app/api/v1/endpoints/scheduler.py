# app/api/v1/endpoints/schedule.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from uuid import UUID
from app.api.v1.dependencies import db_session, current_user
from app.models.schedule import Schedule, ScheduleCreate, ScheduleUpdate
from app.models.user import User
from fastapi import Response
from typing import Any

router = APIRouter(prefix="/users/{user_id}/schedules", tags=["Scheduler"])

# ───────────────────────── helpers
def _own_or_404(session: Session, sid: UUID, user_id: UUID) -> Schedule:
    sched = session.get(Schedule, sid)
    if not sched or sched.user_id != user_id:
        raise HTTPException(404, "Schedule not found")
    return sched

# ───────────────────────── CRUD
@router.get("/", response_model=dict)
def list_schedules(
    user_id: UUID,
    session: Session = db_session(),
    current: User = Depends(current_user)
) -> dict[str, Any]:
    if user_id != current.id:
        raise HTTPException(403, "Forbidden")
    stmt = select(Schedule).where(Schedule.user_id == user_id)
    schedules = session.exec(stmt).all()
    return {"count": len(schedules), "results": schedules}

@router.post("/", response_model=Schedule, status_code=status.HTTP_201_CREATED)
def create_schedule(
    user_id: UUID,
    data: ScheduleCreate,
    session: Session = db_session(),
    current: User = Depends(current_user)
):
    if user_id != current.id:
        raise HTTPException(403, "Forbidden")
    sched = Schedule.model_validate(data, update={"user_id": user_id})
    session.add(sched)
    session.commit()
    session.refresh(sched)
    # TODO: enqueue APScheduler/Celery job here
    return sched

@router.get("/{sid}", response_model=Schedule)
def get_schedule(
    user_id: UUID, sid: UUID,
    session: Session = db_session(),
    current: User = Depends(current_user)
):
    if user_id != current.id:
        raise HTTPException(403, "Forbidden")
    return _own_or_404(session, sid, user_id)

@router.put("/{sid}", response_model=Schedule)
def update_schedule(
    user_id: UUID, sid: UUID,
    data: ScheduleUpdate,
    session: Session = db_session(),
    current: User = Depends(current_user)
):
    if user_id != current.id:
        raise HTTPException(403, "Forbidden")
    sched = _own_or_404(session, sid, user_id)
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(sched, k, v)
    session.add(sched)
    session.commit()
    session.refresh(sched)
    return sched

@router.delete("/{sid}", status_code=204)
def delete_schedule(
    user_id: UUID, sid: UUID,
    session: Session = db_session(),
    current: User = Depends(current_user)
):
    if user_id != current.id:
        raise HTTPException(403, "Forbidden")
    sched = _own_or_404(session, sid, user_id)
    session.delete(sched)
    session.commit()
