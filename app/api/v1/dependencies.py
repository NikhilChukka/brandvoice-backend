from app.core.db import get_session, SYNC_MODE # Remove get_async_session if not used
from fastapi import Depends

# expose a single name so routers stay clean
def db_session():
    return Depends(get_session)


# # app/api/v1/dependencies.py
# from fastapi import Depends
# from app.core.db import get_session, get_async_session, SYNC_MODE

# def db_session():
#     return Depends(get_session if SYNC_MODE else get_async_session)
