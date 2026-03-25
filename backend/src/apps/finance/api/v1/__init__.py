from fastapi import APIRouter
from .payment import router as payment_router

__all__ = ["payment_router"]

router = APIRouter()
router.include_router(payment_router, prefix="/payments", tags=["payments"])
