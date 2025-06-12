from fastapi import APIRouter
from .endpoints import auth, product, scheduler, content, twitter, instagram, facebook, youtube

router = APIRouter()
router.include_router(auth.router)
router.include_router(product.router)
router.include_router(content.router)
router.include_router(scheduler.router)
router.include_router(twitter.router)
router.include_router(instagram.router)
router.include_router(facebook.router)
router.include_router(youtube.router)
# router.include_router(health.router)
