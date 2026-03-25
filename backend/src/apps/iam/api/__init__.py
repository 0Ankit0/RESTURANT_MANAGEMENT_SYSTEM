from fastapi import APIRouter

from .v1 import auth, token_management, rbac, users

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(token_management.router, prefix="/tokens", tags=["tokens"])
api_router.include_router(rbac.router, tags=["rbac"])
api_router.include_router(users.router, tags=["users"])