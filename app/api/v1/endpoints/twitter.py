from fastapi import APIRouter, Depends, HTTPException, Request, Form, UploadFile, File, status
from starlette.responses import RedirectResponse
from app.models.user import User
from app.core.db_dependencies import db_session
from app.api.v1.dependencies import get_current_user
from app.services.twitter_service import post_tweet_for_user
from app.models.firestore_db import FirestoreSession
from typing import List, Optional
import tweepy
from app.core.config import get_settings
import os

router = APIRouter(prefix="/twitter", tags=["Twitter"])

@router.get("/connect")
def twitter_connect(request: Request, user: User = Depends(get_current_user)):
    settings = get_settings()
    auth = tweepy.OAuth1UserHandler(
        settings.twitter_api_key,
        settings.twitter_api_secret,
        callback=settings.twitter_callback_url
    )
    try:
        redirect_url = auth.get_authorization_url()
        # store the request token in the session
        request.session["request_token"] = auth.request_token
        return RedirectResponse(redirect_url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Twitter auth error: {e}")

@router.get("/callback")
async def twitter_callback(
    request: Request,
    session: FirestoreSession = Depends(db_session),
    user: User = Depends(get_current_user)
):
    settings = get_settings()
    request_token = request.session.pop("request_token", None)
    if not request_token:
        raise HTTPException(status_code=400, detail="Missing request token.")
    verifier = request.query_params.get("oauth_verifier")
    if not verifier:
        raise HTTPException(status_code=400, detail="Missing oauth_verifier.")
    
    # Exchange for user tokens
    auth = tweepy.OAuth1UserHandler(
        settings.twitter_api_key,
        settings.twitter_api_secret,
    )
    auth.request_token = request_token
    try:
        access_token, access_token_secret = auth.get_access_token(verifier)
        # Save to user
        update_data = {
            "twitter_access_token": access_token,
            "twitter_access_token_secret": access_token_secret
        }
        await session.update(User, str(user.id), update_data)
        return {"status": "success", "message": "Twitter account connected! You can close this tab."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Twitter callback error: {e}")

@router.post("/post", status_code=status.HTTP_201_CREATED)
async def post_to_twitter(
    text: str = Form(...),
    media: Optional[List[UploadFile]] = File(None),
    session: FirestoreSession = Depends(db_session),
    user: User = Depends(get_current_user)
):
    if not user.twitter_access_token or not user.twitter_access_token_secret:
        raise HTTPException(status_code=400, detail="User has not connected their Twitter account.")
    
    # Save uploaded media temporarily if present
    media_paths = []
    if media:
        for file in media:
            path = f"/tmp/{file.filename}"
            with open(path, "wb") as out:
                out.write(file.file.read())
            media_paths.append(path)
    
    try:
        # Call the v2-based service
        tweet_id = post_tweet_for_user(
            user.twitter_access_token,
            user.twitter_access_token_secret,
            text,
            media_paths
        )
        return {"status": "success", "tweet_id": tweet_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to post tweet: {e}")
    finally:
        for path in media_paths:
            try:
                os.remove(path)
            except:
                pass
