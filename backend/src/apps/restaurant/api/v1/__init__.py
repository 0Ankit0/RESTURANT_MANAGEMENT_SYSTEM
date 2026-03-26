from fastapi import APIRouter

from .operations import router as operations_router

v1_router = APIRouter()
v1_router.include_router(operations_router, tags=["restaurant"])
