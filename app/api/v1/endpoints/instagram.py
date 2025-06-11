from fastapi import APIRouter, Depends, Request, HTTPException, Form, status
from app.models import User
from app.core.config import get_settings
from app.api.v1.dependencies import db_session, current_user
# from app.core.security import get_current_active_user
from sqlalchemy import select
import httpx
from starlette.responses import RedirectResponse
settings = get_settings()

router = APIRouter(prefix="/instagram", tags=["Instagram"])

@router.get('/connect')

def instagram_connect(request: Request, user: User = Depends(current_user)):
    fb_auth_url = "https://www.facebook.com/v23.0/dialog/oauth"
    params = {
        "client_id" : settings.facebook_app_id,
        "redirect_uri" : settings.instagram_callback_url,
        "scope": "pages_show_list,instagram_basic,instagram_content_publish",
        "response_type": "code",
        "state": user.id
    }
    url = httpx.URL(fb_auth_url, params=params)
    return RedirectResponse(str(url))


@router.get("/callback")
async def instagram_callback(
    request: Request,
    code: str| None = None,
    state: str | None = None,
    session = Depends(db_session)):
    if not code or not state:
        raise HTTPException(
            status_code=400,
            detail="Missing code or state parameter in callback.")
    token_url = "https://graph.facebook.com/v23.0/oauth/access_token"
    params = {
        "client_id": settings.facebook_app_id,
        "redirect_uri": settings.instagram_callback_url,
        "client_secret": settings.facebook_app_secret,
        "code": code
    }

    async with httpx.AsyncClient() as client:
        response1 = await client.get(token_url, params = params)
        if response1.status_code != 200:
            raise HTTPException(status_code=response1.status_code,
                                detail="Failed to get access token from Facebook.")
        data = response1.json()
        access_token = data.get("access_token")

    exchange_url = "https://graph.facebook.com/v23.0/oauth/access_token"
    exchange_params = {
        "client_id" : settings.facebook_app_id,
        "grant_type": "fb_exchange_token",
        "fb_exchange_token": access_token,
        "client_secret": settings.facebook_app_secret
    }

    async with httpx.AsyncClient() as client:
        response2 = await client.get(exchange_url, params=exchange_params)
        if response2.status_code != 200:
            raise HTTPException(status_code=response2.status_code,
                                detail="Failed to exchange access token.")
        data = response2.json()
        long_lived_token = data.get("access_token")


     # 2.3 Fetch Page list to get the Page ID
    pages_url = "https://graph.facebook.com/v23.0/me/accounts"
    async with httpx.AsyncClient() as client:
        r3 = await client.get(pages_url, params={"access_token": long_lived_token})
    if r3.status_code != 200 or not (pages := r3.json().get("data")):
        raise HTTPException(status_code=400, detail="Failed to fetch Facebook Pages")
    page_id = pages[0]["id"]  # choose first or let user select

    # 2.4 Get IG Business Account ID
    ig_url = f"https://graph.facebook.com/v23.0/{page_id}"
    async with httpx.AsyncClient() as client:
        r4 = await client.get(ig_url, params={
            "fields": "instagram_business_account",
            "access_token": long_lived_token
        })
    if r4.status_code != 200 or not (ig := r4.json().get("instagram_business_account")):
        raise HTTPException(status_code=400, detail="No Instagram Business account found")
    ig_id = ig["id"]

    # Save the long-lived token to the user
    user = await session.get(User, state)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    user.instagram_page_access_token = long_lived_token
    user.instagram_business_account_id = ig_id
    session.add(user)
    await session.commit()
    return {"status": "connected", "instagram_business_account_id": ig_id}


# 3. Create media container
@router.post("/media", status_code=status.HTTP_201_CREATED)
async def create_media(
    image_url: str = Form(...),
    caption: str | None = Form(None),
    user: User = Depends(current_user),
    session=Depends(db_session)
):
    if not user.instagram_page_access_token or not user.instagram_business_account_id:
        raise HTTPException(400, "Instagram not connected")
    url = f"https://graph.facebook.com/v23.0/{user.instagram_business_account_id}/media"
    params = {
        "image_url": image_url,
        "caption": caption or "",
        "access_token": user.instagram_page_access_token
    }
    async with httpx.AsyncClient() as client:
        r = await client.post(url, data=params)
    if r.status_code != 200:
        raise HTTPException(400, f"Media create failed: {r.text}")
    container_id = r.json()["id"]
    return {"container_id": container_id}


# 4. Poll container status
@router.get("/media/{container_id}/status")
async def media_status(
    container_id: str,
    user: User = Depends(current_user)
):
    if not user.instagram_page_access_token:
        raise HTTPException(400, "Instagram not connected")
    url = f"https://graph.facebook.com/v23.0/{container_id}"
    params = {
        "fields": "status_code",
        "access_token": user.instagram_page_access_token
    }
    async with httpx.AsyncClient() as client:
        r = await client.get(url, params=params)
    if r.status_code != 200:
        raise HTTPException(400, f"Status fetch failed: {r.text}")
    return {"status_code": r.json().get("status_code")}


# 5. Publish container
@router.post("/publish")
async def publish_media(
    container_id: str = Form(...),
    user: User = Depends(current_user)
):
    if not user.instagram_page_access_token or not user.instagram_business_account_id:
        raise HTTPException(400, "Instagram not connected")
    url = f"https://graph.facebook.com/v23.0/{user.instagram_business_account_id}/media_publish"
    params = {
        "container_id": container_id,
        "access_token": user.instagram_page_access_token
    }
    async with httpx.AsyncClient() as client:
        r = await client.post(url, data=params)
    if r.status_code != 200:
        raise HTTPException(400, f"Publish failed: {r.text}")
    return {"media_object_id": r.json()["id"]}
