"""
WebSocket authentication dependency.

JWT is passed as a ``?token=<jwt>`` query parameter (Authorization headers
are not supported in browser WebSocket API).

Returns the authenticated User and the derived AES session key bytes.
Closes the socket with code 4001 on auth failure so the client knows
to re-authenticate rather than retry blindly.
"""
from typing import Optional, Tuple

from fastapi import WebSocket
from jose import JWTError, jwt
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.apps.core import security
from src.apps.core.config import settings
from src.apps.iam.models.token_tracking import TokenTracking
from src.apps.iam.models.user import User
from src.apps.iam.schemas.token import TokenPayload
from src.apps.websocket.crypto import derive_session_key


async def ws_get_current_user(
    websocket: WebSocket,
    db: AsyncSession,
) -> Tuple[User, bytes]:
    """
    Validate the JWT from ``?token=`` and return ``(user, session_key)``.

    ``session_key`` is a 32-byte AES-256-GCM key derived from the token's
    jti + the server SECRET_KEY.  It is unique per token and never travels
    over the network (the client receives only the base64-encoded copy sent
    in the HANDSHAKE frame).

    Closes the WebSocket with code 4001 and raises RuntimeError on failure.
    """
    token: Optional[str] = websocket.query_params.get("token")

    async def _reject(detail: str) -> None:
        await websocket.accept()
        await websocket.send_json({"type": "error", "code": 4001, "detail": detail})
        await websocket.close(code=4001)

    origin = websocket.headers.get("origin")
    if not isinstance(origin, str):
        origin = None
    allowed_origins = {item.strip() for item in settings.WS_ALLOWED_ORIGINS if item.strip()}
    if origin and "*" not in allowed_origins and origin not in allowed_origins:
        await _reject("WebSocket origin is not allowed")
        raise RuntimeError("WS auth failed: origin not allowed")

    if not token:
        await _reject("Missing token")
        raise RuntimeError("WS auth failed: missing token")

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[security.ALGORITHM])
        token_data = TokenPayload(**payload)
    except (JWTError, ValidationError):
        await _reject("Invalid or expired token")
        raise RuntimeError("WS auth failed: invalid token")

    if not token_data.sub:
        await _reject("Invalid token subject")
        raise RuntimeError("WS auth failed: missing sub")

    # Verify the token is still active in the database
    jti = payload.get("jti")
    if jti:
        result = await db.execute(
            select(TokenTracking).where(
                TokenTracking.token_jti == jti,
                TokenTracking.is_active,
            )
        )
        if not result.scalars().first():
            await _reject("Token has been revoked")
            raise RuntimeError("WS auth failed: revoked token")

    # Fetch the user
    result = await db.execute(select(User).where(User.id == int(token_data.sub)))
    user: Optional[User] = result.scalars().first()

    if not user or not user.is_active:
        await _reject("User not found or inactive")
        raise RuntimeError("WS auth failed: user inactive")

    # Derive the per-session AES key from the jti
    session_key = derive_session_key(jti or token_data.sub)

    return user, session_key
