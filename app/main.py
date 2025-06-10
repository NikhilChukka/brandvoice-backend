from dotenv import load_dotenv
import os

# Load .env file from the current directory (app)
# This assumes main.py and .env are in the same directory 'app'
# or that you run the app from the 'app' directory.
# For more robust pathing if running from project root:

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=dotenv_path)
import json
from sqlalchemy.future import select
from fastapi import Request, Form, UploadFile, File, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from typing import List, Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from app.api.v1 import router as api_v1_router
from app.core.config import get_settings
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from app.services.twitter_service import post_tweet_for_user
from app.models.scheduling import ScheduledPost
from app.api.v1.dependencies import db_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from app.core.config import get_settings
from sqlalchemy import create_engine  # <-- sync engine
from sqlmodel import SQLModel

jobstores = {
    "default": SQLAlchemyJobStore(url="sqlite:///./app.db")  # <-- sync URL
}
scheduler = AsyncIOScheduler(jobstores=jobstores)
scheduler.start()
settings = get_settings()
engine: AsyncEngine = create_async_engine(
    settings.database_url,      # e.g. "sqlite+aiosqlite:///./app.db"
    echo=True,
    future=True,
)

def create_db_and_tables():
    """
    Synchronous helper to create all tables.
    SQLModel.metadata is a MetaData object containing all registered tables.
    """
    SQLModel.metadata.create_all  # method reference (for docs)
    # Actual call happens below via run_sync()


async def dispatch_scheduled_tweet(post_id: int):
    async with db_session() as session:
        post = await session.get(ScheduledPost, post_id)
        if not post or post.status != "pending":
            return
        from app.models.user import User
        user = await session.get(User, post.user_id)
        if not user:
            post.status = "failed"
            session.add(post)
            await session.commit()
            return
        media_list = json.loads(post.media_paths) if post.media_paths else None
        try:
            tweet_id = post_tweet_for_user(
                access_token=user.access_token,
                access_token_secret=user.access_token_secret,
                text=post.text,
                media_paths=media_list
            )
            post.status = "sent"
        except Exception:
            post.status = "failed"
        session.add(post)
        await session.commit()

def create_app() -> FastAPI:
    s = get_settings()
    app = FastAPI(
        title=s.app_name,
        version="1.0.0",
        description="Multi-agent content automation backend",
        docs_url="/docs", redoc_url="/redoc"
    )

    @app.on_event("startup")
    async def on_startup():
    # Establish a transaction and run the sync create_all() call
        async with engine.begin() as conn:
            # This runs: SQLModel.metadata.create_all(engine)
            await conn.run_sync(SQLModel.metadata.create_all)
    on_startup.__doc__ = "Create database tables on startup"

    async def load_scheduled_posts():
        # On startup, load any pending posts into the scheduler
        async with db_session() as session:  # AsyncSession
            result = await session.execute(
                select(ScheduledPost).filter_by(status="pending")
            )
            for post in result.scalars():
                scheduler.add_job(
                    func=dispatch_scheduled_tweet,
                    trigger="date",
                    run_date=post.run_at,
                    args=[post.id],
                    id=str(post.id),
                    replace_existing=True,
                )
    load_scheduled_posts.__doc__ = "Load pending scheduled posts into the scheduler on startup"
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=s.allow_origins, allow_credentials=True,
        allow_methods=["*"], allow_headers=["*"],
    )
    app.add_middleware(
        SessionMiddleware,
        secret_key=s.secret_key or "change-this-secret-key",
        session_cookie="session",
        max_age=60*60*24*7,  # 1 week
    )
    app.include_router(api_v1_router, prefix="/api/v1", tags=["v1"])

    return app

app = create_app()
