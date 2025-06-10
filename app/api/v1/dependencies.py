from fastapi import Depends
from app.core.db import get_async_session, get_session

def db_session_sync():
    gen = get_session()
    session = next(gen)
    try:
        yield session
    finally:
        session.close()

async def db_session_async():
    agen = get_async_session()
    session = await agen.__anext__()
    try:
        yield session
    finally:
        await session.close()

if get_async_session is not None:
    db_session = db_session_async
else:
    db_session = db_session_sync

from app.models.user import User
from app.core.security import get_current_active_user

def current_user(user: User = Depends(get_current_active_user)) -> User:
    return user
