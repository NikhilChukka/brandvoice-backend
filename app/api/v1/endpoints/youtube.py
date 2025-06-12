from fastapi import APIRouter, Depends, HTTPException, Request, Form, UploadFile, File

from app.core.config import get_settings
from app.models.user import User
from app.api.v1.dependencies import db_session, current_user
import httpx
from starlette.responses import RedirectResponse
from app.services.youtube_service import upload_video_for_user
import os
router = APIRouter(prefix="/youtube", tags=["YouTube"])
settings = get_settings()

auth_url = "https://accounts.google.com/o/oauth2/v2/auth"

@router.get("/connect")
async def youtube_connect(request : Request, user :User = Depends(current_user)):
    params = {
        "client_id": settings.youtube_client_id,
        "redirect_uri": settings.youtube_callback_url,
        "scope": "https://www.googleapis.com/auth/youtube.upload",
        "response_type": "code",
        "state": user.id,
        "prompt": "consent",
        "access_type": "offline",
    }
    url = httpx.URL(auth_url, params=params)
    return RedirectResponse(str(url))


@router.get("/callback")
async def youtube_callback(code: str, state: str, session=Depends(db_session)):
    if not code or not state:
        raise HTTPException(
            status_code=400,
            detail="Missing code or state parameter in callback."
        )
    
    token_url = "https://oauth2.googleapis.com/token"
    params = {
        "client_id": settings.youtube_client_id,
        "client_secret": settings.youtube_client_secret,
        "redirect_uri": settings.youtube_callback_url,
        "code": code,
        "grant_type": "authorization_code",
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, data=params)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to get access token from Google.")
        
        data = response.json()
        access_token = data.get("access_token")
        refresh_token = data.get("refresh_token")

    user = await session.get(User, state)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    
    user.youtube_access_token = access_token
    user.youtube_refresh_token = refresh_token
    session.add(user)
    await session.commit()

    return {"status": "success", "message": "YouTube account connected! You can close this tab."}



@router.post("/video", status_code=201)
async def youtube_video(
    title: str = Form(...),
    description: str = Form(""),
    file: UploadFile = File(...),
    user: User = Depends(current_user)):
    path = f"/tmp/{file.filename}"
    with open(path, "wb") as f:
        f.write(await file.read())
    video_id = await upload_video_for_user(user, path, title, description)
    os.remove(path)
    return {"video_id": video_id}