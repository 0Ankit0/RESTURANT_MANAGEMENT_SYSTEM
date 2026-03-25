from fastapi import APIRouter

from .v1 import router as v1_router

notification_router = APIRouter()
notification_router.include_router(v1_router, prefix="/notifications", tags=["notifications"])
