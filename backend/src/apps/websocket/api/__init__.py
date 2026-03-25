from fastapi import APIRouter
from .v1 import router as v1_router

ws_router = APIRouter()
ws_router.include_router(v1_router, prefix="/ws")
