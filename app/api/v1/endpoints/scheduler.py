# app/api/v1/endpoints/scheduler.py
from fastapi import APIRouter, Depends, HTTPException, status, Form, File, UploadFile
from datetime import datetime
from typing import List, Dict, Any
from uuid import UUID
from app.core.db_dependencies import get_db
from app.api.v1.dependencies import get_current_user
from app.models.schedule import Schedule, ScheduleCreate, ScheduleUpdate
from app.models.user import User
from app.models.firestore_db import FirestoreSession
from app.models.enums import Platform, ScheduleState
import json
import uuid

router = APIRouter()

@router.get("/", response_model=List[Schedule])
async def list_schedules(
    user_id: str,
    db: FirestoreSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all schedules for the current user."""
    if user_id != str(current_user.id):
        raise HTTPException(403, "Not allowed to access this user's schedules")
    
    schedules = await db.query(
        "schedules",
        filters=[("user_id", "==", user_id)]
    )
    return schedules

@router.post("/", response_model=Schedule, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    user_id: str,
    data: ScheduleCreate,
    db: FirestoreSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new schedule."""
    if user_id != str(current_user.id):
        raise HTTPException(403, "Not allowed to access this user's schedules")
    
    # content = await db.get("content", str(data.content_id))
    # if not content:
    #     raise HTTPException(404, "Content item not found")
    
    schedule_data = data.model_dump()
    schedule_data["content_id"] = str(data.content_id) if data.content_id else None
    schedule_data["user_id"] = user_id
    schedule_data["status"] = ScheduleState.scheduled
    schedule_data["created_at"] = datetime.utcnow()
    schedule_data["modified_at"] = datetime.utcnow()
    
    doc_id = await db.add("schedules", schedule_data)
    return {**schedule_data, "id": doc_id}

@router.get("/{schedule_id}", response_model=Schedule)
async def get_schedule(
    user_id: str,
    schedule_id: str,
    db: FirestoreSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific schedule."""
    if user_id != str(current_user.id):
        raise HTTPException(403, "Not allowed to access this user's schedules")
    
    schedule = await db.get("schedules", schedule_id)
    if not schedule:
        raise HTTPException(404, "Schedule not found")
    
    if schedule["user_id"] != user_id:
        raise HTTPException(403, "Not authorized to access this schedule")
    
    return schedule

@router.put("/{schedule_id}", response_model=Schedule)
async def update_schedule(
    user_id: str,
    schedule_id: str,
    data: ScheduleUpdate,
    db: FirestoreSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a schedule."""
    if user_id != str(current_user.id):
        raise HTTPException(403, "Not allowed to access this user's schedules")
    
    schedule = await db.get("schedules", schedule_id)
    if not schedule:
        raise HTTPException(404, "Schedule not found")
    
    if schedule["user_id"] != user_id:
        raise HTTPException(403, "Not authorized to update this schedule")
    
    update_data = data.model_dump(exclude_unset=True)
    update_data["modified_at"] = datetime.utcnow()
    await db.update("schedules", schedule_id, update_data)
    
    updated_schedule = await db.get("schedules", schedule_id)
    return updated_schedule

@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    user_id: str,
    schedule_id: str,
    db: FirestoreSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a schedule."""
    if user_id != str(current_user.id):
        raise HTTPException(403, "Not allowed to access this user's schedules")
    
    schedule = await db.get("schedules", schedule_id)
    if not schedule:
        raise HTTPException(404, "Schedule not found")
    
    if schedule["user_id"] != user_id:
        raise HTTPException(403, "Not authorized to delete this schedule")
    
    await db.delete("schedules", schedule_id)

# @router.post("/schedule", status_code=status.HTTP_201_CREATED)
# async def schedule_post(
#     user_id: str,
#     platform: Platform = Form(...),
#     content: str = Form(...),
#     run_at: datetime = Form(...),
#     timezone: str = Form(...),
#     media: list[UploadFile] | None = File(None),
#     db: FirestoreSession = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """Schedule a post for later publication."""
#     if user_id != str(current_user.id):
#         raise HTTPException(403, "Not allowed to access this user's schedules")
    
#     paths = []
#     if media:
#         for file in media:
#             # Handle file upload and get path
#             paths.append(f"path/to/{file.filename}")
    
#     post_data = {
#         "user_id": user_id,
#         "platform": platform,
#         "content": content,
#         "run_at": run_at.isoformat(),
#         "timezone": timezone,
#         "media_paths": paths,
#         "status": ScheduleState.upcoming,
#         "created_at": datetime.utcnow(),
#         "modified_at": datetime.utcnow()
#     }
    
#     doc_id = await db.add("scheduled_posts", post_data)
    
#     return {"id": doc_id, **post_data} 