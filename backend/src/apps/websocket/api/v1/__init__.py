from fastapi import APIRouter
from .ws import router as ws_router

router = APIRouter()
router.include_router(ws_router)
