from fastapi import APIRouter, Depends, HTTPException, Request, Form, status
from starlette.responses import RedirectResponse
from app.models import User
from app.api.v1.dependencies import db_session, current_user
from app.services import facebook_service as fb
from app.services.facebook_service import post_video
from sqlmodel import Session
import httpx
from app.core.config import get_settings
settings = get_settings()

router = APIRouter(prefix="/facebook", tags=["Facebook"])

# ---------- OAuth connect ---------- #
@router.get("/connect")
def fb_connect(request: Request, user: User = Depends(current_user)):
    params = {
        "client_id": settings.facebook_app_id,
        "redirect_uri": settings.facebook_callback_url,
        "scope": "pages_show_list,pages_manage_posts,pages_read_engagement",
        "response_type": "code",
        "state": user.id,
    }
    url = httpx.URL("https://www.facebook.com/v23.0/dialog/oauth", params=params)
    return RedirectResponse(str(url))


@router.get("/callback")
async def fb_callback(
    code: str | None = None,
    state: str | None = None,
    session: Session = Depends(db_session),
):
    if not code or not state:
        raise HTTPException(400, "Missing code/state")
    short_token = await fb.exchange_code_for_token(code)
    long_token = await fb.upgrade_to_long_lived(short_token)
    page_id, page_token = await fb.page_id_and_token(long_token)

    user = await session.get(User, state)
    if not user:
        raise HTTPException(404, "User not found")
    user.fb_page_id = page_id
    user.fb_page_access_token = page_token
    session.add(user)
    await session.commit()
    return {"status": "connected", "page_id": page_id}


# ---------- posting ---------- #
@router.post("/post")
async def post_message(
    message: str = Form(...),
    link: str | None = Form(None),
    user: User = Depends(current_user),
):
    if not user.fb_page_id or not user.fb_page_access_token:
        raise HTTPException(400, "Facebook not connected")
    post_id = await fb.post_feed(user.fb_page_id, user.fb_page_access_token, message, link)
    return {"post_id": post_id}


@router.post("/photo")
async def post_photo(
    image_url: str = Form(...),
    caption: str | None = Form(None),
    user: User = Depends(current_user),
):
    if not user.fb_page_id or not user.fb_page_access_token:
        raise HTTPException(400, "Facebook not connected")
    photo_id = await fb.post_photo(user.fb_page_id, user.fb_page_access_token, image_url, caption)
    return {"photo_id": photo_id}


@router.post("/video")
async def post_videos(
    video_url : str = Form(...),
    user : User = Depends(current_user),
    description: str | None = Form(None)):

    if not user.fb_page_id or not user.fb_page_access_token:
        raise HTTPException(400, "Facebook not connected")

    try:
        vid_id = await post_video(
            user.fb_page_id,
            user.fb_page_access_token,
            video_url,
            description,
        )
        return {"video_id": vid_id}
    except httpx.HTTPStatusError as exc:
        raise HTTPException(400, f"Video publish failed: {exc.response.text}")
    


# app/api/v1/facebook.py  (add below /photo)
@router.post("/video_post", status_code=status.HTTP_201_CREATED)
async def post_video_feed(
    video_url: str = Form(...),
    message: str | None = Form(None),
    user: User = Depends(current_user),
):
    if not user.fb_page_id or not user.fb_page_access_token:
        raise HTTPException(400, "Facebook not connected")
    try:
        post_id = await fb.post_video_as_feed(
            user.fb_page_id,
            user.fb_page_access_token,
            video_url,
            message or "",
        )
        return {"post_id": post_id}
    except httpx.HTTPStatusError as exc:
        raise HTTPException(400, f"Video feed post failed: {exc.response.text}")
