"""Request and token utility helpers."""
from datetime import datetime
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import and_, update

from src.apps.iam.models.token_tracking import TokenTracking


def get_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    return request.client.host if request.client else "unknown"


async def revoke_tokens_for_ip(
    db: AsyncSession,
    user_id: int,
    ip_address: str,
    reason: str = "New token issued for same IP",
) -> None:
    await db.execute(
        update(TokenTracking)
        .where(and_(
            TokenTracking.user_id == user_id,
            TokenTracking.ip_address == ip_address,
            TokenTracking.is_active == True,
        ))
        .values(is_active=False, revoked_at=datetime.now(), revoke_reason=reason)
    )
