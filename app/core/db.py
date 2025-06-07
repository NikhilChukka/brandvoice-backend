import os
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from .config import get_settings # MODIFIED

_settings = get_settings() # Use the imported get_settings

DATABASE_URL = _settings.database_url # MODIFIED to use the settings object
if DATABASE_URL is None:
    raise ValueError("DATABASE_URL environment variable is not set or not loaded via settings.")

# ---- choose sync or async --------------------------------------------------
SYNC_MODE = not _settings.database_url.startswith("postgresql+asyncpg")

if SYNC_MODE:
    engine = create_engine(DATABASE_URL, echo=False)
    def get_session():
        with Session(engine) as session:
            yield session
else:
    async_engine = create_async_engine(DATABASE_URL, echo=False)

    async def get_async_session():
        async with AsyncSession(async_engine) as session:
            yield session
