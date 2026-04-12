"""Request and token utility helpers."""
from datetime import datetime, timezone
from typing import Iterable
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
) -> int:
    return await revoke_active_tokens(
        db=db,
        user_id=user_id,
        reason=reason,
        ip_address=ip_address,
    )


async def revoke_active_tokens(
    db: AsyncSession,
    user_id: int,
    reason: str,
    ip_address: str | None = None,
    exclude_jtis: Iterable[str] | None = None,
) -> int:
    filters = [TokenTracking.user_id == user_id, TokenTracking.is_active == True]
    if ip_address:
        filters.append(TokenTracking.ip_address == ip_address)
    if exclude_jtis:
        filters.append(TokenTracking.token_jti.notin_(list(exclude_jtis)))

    result = await db.execute(
        update(TokenTracking)
        .where(and_(*filters))
        .values(
            is_active=False,
            revoked_at=datetime.now(timezone.utc),
            revoke_reason=reason,
        )
    )
    return int(result.rowcount or 0)
