import asyncio
import os
import aiohttp
from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.models.firestore_db import FirestoreSession
from app.models.enums import ScheduleState
from app.services.facebook_service import post_feed, post_photo, post_video
from app.services.twitter_service import post_tweet_for_user
from app.services.youtube_service import upload_video_for_user

async def download_file(url, dest):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                with open(dest, 'wb') as f:
                    f.write(await resp.read())
                return dest
            else:
                raise Exception(f"Failed to download file: {url}")

async def post_to_instagram(cred, image_url, video_url, caption):
    # Instagram Graph API: create media container, then publish
    async with aiohttp.ClientSession() as session:
        if video_url:
            url = f"https://graph.facebook.com/v23.0/{cred['instagram_account_id']}/media"
            params = {
                "media_type": "VIDEO",
                "video_url": video_url,
                "caption": caption,
                "access_token": cred["access_token"]
            }
            async with session.post(url, data=params) as resp:
                data = await resp.json()
                container_id = data.get("id")
            pub_url = f"https://graph.facebook.com/v23.0/{cred['instagram_account_id']}/media_publish"
            pub_params = {
                "creation_id": container_id,
                "access_token": cred["access_token"]
            }
            async with session.post(pub_url, data=pub_params) as resp:
                pub_data = await resp.json()
            return pub_data
        elif image_url:
            url = f"https://graph.facebook.com/v23.0/{cred['instagram_account_id']}/media"
            params = {
                "image_url": image_url,
                "caption": caption,
                "access_token": cred["access_token"]
            }
            async with session.post(url, data=params) as resp:
                data = await resp.json()
                container_id = data.get("id")
            pub_url = f"https://graph.facebook.com/v23.0/{cred['instagram_account_id']}/media_publish"
            pub_params = {
                "creation_id": container_id,
                "access_token": cred["access_token"]
            }
            async with session.post(pub_url, data=pub_params) as resp:
                pub_data = await resp.json()
            return pub_data
        else:
            raise Exception("No image or video URL for Instagram post.")

async def process_due_schedules():
    db = FirestoreSession()
    now = datetime.now(timezone.utc)
    print(f"*** Checking for schedules due at or before: {now.isoformat()} ***")
    
    due_schedules = await db.query(
        "schedules",
        filters=[("run_at", "<=", now), ("status", "==", ScheduleState.upcoming)]
    )
    print(f"*** Found {len(due_schedules)} due schedules ***")
    
    for sched in due_schedules:
        user_id = sched["user_id"]
        product_id = sched.get("product_id")
        product = None
        if product_id:
            product_doc = await db.get("products", product_id)
            if product_doc:
                product = product_doc
        if not product:
            await db.update("schedules", sched["id"], {"status": ScheduleState.failed, "results": {"error": "Product not found"}})
            continue

        results = {}
        for platform in sched["platforms"]:
            try:
                marketing_platform = product.get("marketing_platform", {})
                platform_data = marketing_platform.get(platform, {})

                content = platform_data.get("content", {})
                caption = content.get("caption") or ""
                call_to_action = content.get("call_to_action") or ""
                hashtags = content.get("hashtags") or []
                if isinstance(hashtags, str):
                    hashtags = hashtags.split()
                hashtags_str = " ".join(hashtags)

                image_url = platform_data.get("image_url")
                video_url = platform_data.get("video_url")
                message = f"{caption}\n\n{call_to_action}\n\n{hashtags_str}".strip()

                # --- Facebook ---
                if platform == "facebook":
                    creds = await db.query("facebook_credentials", filters=[("user_id", "==", user_id), ("is_active", "==", True)])
                    if creds:
                        cred = creds[0]
                        if video_url:
                            await post_video(cred["page_id"], cred["access_token"], video_url, description=message)
                            results["facebook"] = "video_success"
                        elif image_url:
                            await post_photo(cred["page_id"], cred["access_token"], image_url, caption=message)
                            results["facebook"] = "image_success"
                        else:
                            await post_feed(cred["page_id"], cred["access_token"], message)
                            results["facebook"] = "text_success"
                    else:
                        results["facebook"] = "no_credentials"

                # --- Instagram ---
                elif platform == "instagram":
                    creds = await db.query("instagram_credentials", filters=[("user_id", "==", user_id), ("is_active", "==", True)])
                    if creds:
                        cred = creds[0]
                        await post_to_instagram(cred, image_url, video_url, message)
                        results["instagram"] = "success"
                    else:
                        results["instagram"] = "no_credentials"

                # --- Twitter ---
                elif platform == "twitter" or platform == "x":
                    creds = await db.query("twitter_credentials", filters=[("user_id", "==", user_id), ("is_active", "==", True)])
                    if creds:
                        cred = creds[0]
                        media_paths = []
                        # Download image for Twitter if present
                        if image_url:
                            filename = f"/tmp/{product_id}_twitter_image.jpg"
                            await download_file(image_url, filename)
                            media_paths.append(filename)
                        # Download video for Twitter if present (optional, if supported)
                        # if video_url:
                        #     filename = f"/tmp/{product_id}_twitter_video.mp4"
                        #     await download_file(video_url, filename)
                        #     media_paths.append(filename)
                        await post_tweet_for_user(
                            cred["access_token"],
                            cred["access_token_secret"],
                            message,
                            media_paths if media_paths else None
                        )
                        for path in media_paths:
                            try:
                                os.remove(path)
                            except Exception:
                                pass
                        results["twitter"] = "success"
                    else:
                        results["twitter"] = "no_credentials"

                # --- YouTube ---
                elif platform == "youtube":
                    creds = await db.query("youtube_credentials", filters=[("user_id", "==", user_id)])
                    if creds and video_url:
                        cred = creds[0]
                        filename = f"/tmp/{product_id}_yt_video.mp4"
                        await download_file(video_url, filename)
                        # You may need to adapt this if your upload_video_for_user expects a user object
                        await upload_video_for_user(
                            cred,  # adapt as needed
                            filename,
                            title=caption,
                            desc=call_to_action
                        )
                        os.remove(filename)
                        results["youtube"] = "success"
                    else:
                        results["youtube"] = "no_credentials_or_no_video"

            except Exception as e:
                results[platform] = f"error: {str(e)}"

        # Update schedule status
        if all("success" in v for v in results.values() if not v.startswith("no_")):
            await db.update("schedules", sched["id"], {"status": ScheduleState.published, "results": results})
        else:
            await db.update("schedules", sched["id"], {"status": ScheduleState.failed, "results": results})

# Optional: Migration utility to convert run_at from string to timestamp for existing schedules
async def migrate_run_at_to_timestamp():
    db = FirestoreSession()
    schedules = await db.query("schedules", filters=[])
    for sched in schedules:
        run_at = sched.get("run_at")
        if isinstance(run_at, str):
            try:
                # Try parsing ISO string to datetime
                dt = datetime.fromisoformat(run_at.replace("Z", "+00:00"))
                await db.update("schedules", sched["id"], {"run_at": dt})
                print(f"Migrated schedule {sched['id']} run_at to timestamp.")
            except Exception as e:
                print(f"Failed to migrate schedule {sched['id']}: {e}")

async def main():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(process_due_schedules, 'interval', seconds=10)
    scheduler.start()
    print("Scheduler started. Press Ctrl+C to exit.")
    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        pass

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "migrate":
        asyncio.run(migrate_run_at_to_timestamp())
    else:
        asyncio.run(main())