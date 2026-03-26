from fastapi import APIRouter

from .v1 import v1_router

restaurant_router = APIRouter()
restaurant_router.include_router(v1_router)
