from app.core.db import get_session, SYNC_MODE # Remove get_async_session if not used
from fastapi import Depends
from app.core.security import get_current_active_user # Corrected import path

# expose a single name so routers stay clean
def db_session():
    return Depends(get_session)


# app/api/v1/dependencies.py  (add)
from app.models.user import User


# This function now correctly uses get_current_active_user from app.core.security
def current_user(user: User = Depends(get_current_active_user)) -> User:
    return user
