from fastapi import APIRouter
from .tenant import router as tenant_router

v1_router = APIRouter()
v1_router.include_router(tenant_router, prefix="/tenants", tags=["tenants"])
