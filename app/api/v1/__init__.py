from fastapi import APIRouter
from .endpoints import auth, product, scheduler, content, health

router = APIRouter()
router.include_router(auth.router)
router.include_router(product.router)
router.include_router(content.router)
router.include_router(scheduler.router)
# router.include_router(health.router)
