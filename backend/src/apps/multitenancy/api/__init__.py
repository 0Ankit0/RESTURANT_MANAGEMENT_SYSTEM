from fastapi import APIRouter
from .v1 import v1_router

multitenancy_router = APIRouter()
multitenancy_router.include_router(v1_router)
