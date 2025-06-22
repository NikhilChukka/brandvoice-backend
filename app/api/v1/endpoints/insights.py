from __future__ import annotations

"""
insights.py – Cross‑platform metrics aggregator
==============================================
• **NEW:** helpers no longer depend on *cached post IDs*.  Instead they fetch
  recent items at runtime:
  ─ **Twitter** → `/2/users/{twitter_account_id}/tweets?max_results=20&tweet.fields=public_metrics`  ➜ sums `impression_count` & `url_link_clicks`.
  ─ **YouTube** → `search.list` to grab most‑recent 20 uploads, then one
    `videos.list` call to collect statistics.

• Credentials are stored in dedicated tables; we introspect them to discover
  required IDs (e.g. `twitter_account_id`, `youtube_channel_id`).  Update your
  credential models accordingly if those fields are named differently.
"""

import asyncio
from datetime import timedelta
from typing import Coroutine, Callable, List, Dict

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.api.v1.dependencies import db_session, current_user
from app.models.user import User
from app.models.facebook import FacebookCredentialBase
from app.models.twitter import TwitterCredential
from app.models.instagram import InstagramCredentialBase
from app.models.youtube import YouTubeCredentialBase

# ────────────────────────────────────────────────────────────────────────
router = APIRouter(prefix="/api/v1", tags=["Insights"])

# ────────────────────────────────────────────────────────────────────────
#  Utility: generic async back‑off wrapper
# ────────────────────────────────────────────────────────────────────────

def retry_async(max_attempts: int = 3, base_delay: float = 1.0):
    """Exponential back‑off for 429/5xx."""

    def decorator(fn: Callable[..., Coroutine]):  # type: ignore[override]
        async def wrapper(*args, **kwargs):  # type: ignore[override]
            attempt = 0
            while True:
                try:
                    return await fn(*args, **kwargs)
                except httpx.HTTPStatusError as exc:
                    if exc.response.status_code in {429, 500, 502, 503, 504} and attempt < max_attempts:
                        await asyncio.sleep(base_delay * (2 ** attempt))
                        attempt += 1
                        continue
                    raise
        return wrapper

    return decorator


# ────────────────────────────────────────────────────────────────────────
#  Merge helpers
# ────────────────────────────────────────────────────────────────────────

def merge_metrics(results: List[Dict[str, float]]) -> Dict:
    totals = {"views": 0.0, "clicks": 0.0}
    for r in results:
        totals["views"] += r.get("views", 0)
        totals["clicks"] += r.get("clicks", 0)
    totals["ctr"] = (totals["clicks"] / totals["views"] * 100) if totals["views"] else 0
    return {"totals": totals, "platforms": results}


# ────────────────────────────────────────────────────────────────────────
#  Per‑platform insight helpers (no cached IDs required)
# ────────────────────────────────────────────────────────────────────────

TW_BASE_V2 = "https://api.twitter.com/2"

@retry_async()
async def twitter_overview(creds: TwitterCredential) -> Dict[str, float]:
    """Fetch last 20 tweets for the authorised account and aggregate metrics."""
    if not (acct_id := getattr(creds, "twitter_account_id", None)):
        # Optionally call /users/me to discover ID once and persist it.
        headers = {"Authorization": f"Bearer {creds.access_token}"}
        async with httpx.AsyncClient() as c:
            me = await c.get(f"{TW_BASE_V2}/users/me", headers=headers)
            acct_id = me.json().get("data", {}).get("id")
    if not acct_id:
        return {"platform": "twitter", "views": 0, "clicks": 0}

    url = f"{TW_BASE_V2}/users/{acct_id}/tweets?max_results=20&tweet.fields=public_metrics"
    headers = {"Authorization": f"Bearer {creds.access_token}"}
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.get(url, headers=headers)
        r.raise_for_status()
    metrics = [t["public_metrics"] for t in r.json().get("data", [])]
    views = sum(m.get("impression_count", 0) for m in metrics)
    clicks = sum(m.get("url_link_clicks", 0) for m in metrics)
    return {"platform": "twitter", "views": views, "clicks": clicks}


@retry_async()
async def facebook_overview(creds: FacebookCredentialBase) -> Dict[str, float]:
    url = f"https://graph.facebook.com/v18.0/{creds.page_id}/insights"
    params = {"metric": "page_impressions,page_total_actions", "access_token": creds.access_token}
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.get(url, params=params)
        r.raise_for_status()
    data = {d["name"]: int(d["values"][0]["value"]) for d in r.json()["data"]}
    return {"platform": "facebook", "views": data.get("page_impressions", 0), "clicks": data.get("page_total_actions", 0)}


@retry_async()
async def instagram_overview(creds: InstagramCredentialBase) -> Dict[str, float]:
    url = f"https://graph.facebook.com/v18.0/{creds.instagram_account_id}/insights"
    params = {"metric": "impressions,reach", "access_token": creds.access_token}
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.get(url, params=params)
        r.raise_for_status()
    d = {i["name"]: int(i["values"][0]["value"]) for i in r.json()["data"]}
    return {"platform": "instagram", "views": d.get("impressions", 0), "clicks": 0}


@retry_async()
async def youtube_overview(creds: YouTubeCredentialBase) -> Dict[str, float]:
    """List most‑recent 20 uploads, then sum view counts."""
    channel_id = getattr(creds, "youtube_channel_id", None)
    if not channel_id:
        return {"platform": "youtube", "views": 0, "clicks": 0}

    # 1️⃣  search.list – find latest 20 video IDs
    search_params = {
        "part": "id",
        "channelId": channel_id,
        "maxResults": 20,
        "order": "date",
        "type": "video",
        "key": creds.api_key,
    }
    async with httpx.AsyncClient(timeout=30) as c:
        s = await c.get("https://www.googleapis.com/youtube/v3/search", params=search_params)
        s.raise_for_status()
    ids = ",".join(i["id"]["videoId"] for i in s.json().get("items", []))
    if not ids:
        return {"platform": "youtube", "views": 0, "clicks": 0}

    # 2️⃣  videos.list – grab statistics in one call
    video_params = {"part": "statistics", "id": ids, "key": creds.api_key}
    async with httpx.AsyncClient(timeout=30) as c:
        v = await c.get("https://www.googleapis.com/youtube/v3/videos", params=video_params)
        v.raise_for_status()
    views = sum(int(item["statistics"].get("viewCount", 0)) for item in v.json().get("items", []))
    return {"platform": "youtube", "views": views, "clicks": 0}


async def mailchimp_overview(_: object) -> Dict[str, float]:
    return {"platform": "mailchimp", "views": 0, "clicks": 0}


# ────────────────────────────────────────────────────────────────────────
#  Main route – gather helpers in parallel
# ────────────────────────────────────────────────────────────────────────

@router.get("/insights/overview", status_code=status.HTTP_200_OK)
async def insights_overview(
    user: User = Depends(current_user),
    session: Session = Depends(db_session),
):
    tasks: List[Coroutine] = []

    if tw := session.exec(select(TwitterCredential).where(TwitterCredential.user_id == user.id)).first():
        tasks.append(twitter_overview(tw))

    if fb := session.exec(select(FacebookCredentialBase).where(FacebookCredentialBase.user_id == user.id)).first():
        tasks.append(facebook_overview(fb))

    if ig := session.exec(select(InstagramCredentialBase).where(InstagramCredentialBase.user_id == user.id)).first():
        tasks.append(instagram_overview(ig))

    if yt := session.exec(select(YouTubeCredentialBase).where(YouTubeCredentialBase.user_id == user.id)).first():
        tasks.append(youtube_overview(yt))

    # Add mailchimp creds when table defined
    # if mc := session.exec(select(MailchimpCredentials).where(MailchimpCredentials.user_id == user.id)).first():
    #     tasks.append(mailchimp_overview(mc))

    if not tasks:
        raise HTTPException(400, "User has no connected platforms")

    raw = await asyncio.gather(*tasks, return_exceptions=True)
    ok = [r for r in raw if not isinstance(r, Exception)]
    return merge_metrics(ok)
