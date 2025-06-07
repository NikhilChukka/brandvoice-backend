from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from uuid import UUID
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from app.api.v1.dependencies import db_session
from app.models.schedule import Schedule, ScheduleCreate

router = APIRouter(prefix="/schedules", tags=["Scheduler"])

# ---- APScheduler singleton -------------------------------------------------
scheduler = BackgroundScheduler(timezone="UTC")
scheduler.start()

def _publish_job(schedule_id: str):
    # TODO: integrate with your ADK SchedulerAgent
    print(f"[{datetime.utcnow().isoformat()}] Publishing job {schedule_id}")

# ---- routes ----------------------------------------------------------------
@router.post("/", response_model=Schedule, status_code=status.HTTP_201_CREATED)
def create_schedule(
    data: ScheduleCreate,
    session: Session = Depends(db_session)
):
    sched = Schedule.model_validate(data)
    session.add(sched)
    session.commit()
    session.refresh(sched)

    scheduler.add_job(
        _publish_job,
        "date",
        id=str(sched.id),
        run_date=sched.run_at,
        args=[str(sched.id)],
        replace_existing=True,
    )
    return sched

@router.get("/", response_model=list[Schedule])
def list_schedules(session: Session = Depends(db_session)):
    return session.exec(select(Schedule)).all()

@router.delete("/{sid}", status_code=204)
def cancel_schedule(sid: UUID, session: Session = Depends(db_session)):
    sched = session.get(Schedule, sid)
    if not sched:
        raise HTTPException(404, "Schedule not found")

    scheduler.remove_job(str(sid))
    sched.state = "cancelled"
    session.add(sched)
    session.commit()
