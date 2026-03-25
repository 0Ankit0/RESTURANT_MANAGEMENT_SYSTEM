from fastapi import APIRouter
from .v1 import router as v1_router

finance_router = APIRouter()
finance_router.include_router(v1_router)
