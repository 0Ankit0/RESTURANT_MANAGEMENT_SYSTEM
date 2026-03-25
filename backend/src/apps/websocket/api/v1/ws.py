"""
WebSocket route handlers + supporting REST endpoints.

WebSocket endpoints
───────────────────
  WS  /ws/                      — global connection (receives personal events)
  WS  /ws/room/{room}/          — join a named room (receives room + personal events)

REST endpoints
──────────────
  GET /ws/stats/                — connection counts (authenticated)
  GET /ws/online/{user_id}/     — check if a user is currently connected

Encryption handshake
─────────────────────
1. Client connects with ``?token=<jwt>``.
2. Server authenticates, then sends a plaintext HANDSHAKE frame:
       {"type": "handshake", "session_key": "<base64-32-bytes>"}
3. All subsequent frames in both directions are ``WSEncryptedFrame``:
       {"type": "<msg_type>", "iv": "<b64-nonce>", "data": "<b64-ciphertext>"}
   where ``data`` decrypts to the JSON of the actual message model.
"""
import asyncio
import logging

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.core.config import settings
from src.apps.iam.api.deps import get_current_user, get_db
from src.apps.iam.models.user import User
from src.apps.iam.utils.hashid import decode_id_or_404, encode_id
from src.apps.websocket.crypto import session_key_b64
from src.apps.websocket.deps import ws_get_current_user
from src.apps.websocket.manager import manager
from src.apps.websocket.schemas.messages import (
    WSAckMessage,
    WSBroadcastMessage,
    WSErrorMessage,
    WSHandshakeMessage,
    WSJoinRoomMessage,
    WSLeaveRoomMessage,
    WSMessagePayload,
    WSMessageType,
    WSPongMessage,
    WSRoomMessage,
    WSOnlineStatusResponse,
    WSStatsResponse,
    WSTypingMessage,
)

log = logging.getLogger(__name__)
router = APIRouter()


async def _heartbeat_loop(user_id: int) -> None:
    while True:
        await asyncio.sleep(settings.WS_HEARTBEAT_INTERVAL_SECONDS)
        await manager.send_personal_model(user_id, WSPongMessage())


# ──────────────────────────────────────────────────────────────────────────────
# Shared connection handler
# ──────────────────────────────────────────────────────────────────────────────

async def _handle_connection(
    websocket: WebSocket,
    db: AsyncSession,
    initial_room: str | None = None,
) -> None:
    """
    Core WebSocket connection loop (shared by both endpoints).

    1. Authenticate via JWT query param.
    2. Accept + register connection with the session key.
    3. Send HANDSHAKE frame with the base64 session key.
    4. If initial_room provided, join that room automatically.
    5. Receive → decrypt → dispatch loop.
    """
    try:
        user, session_key = await ws_get_current_user(websocket, db)
    except RuntimeError:
        return  # already closed by ws_get_current_user

    await manager.connect(websocket, user.id, session_key)

    # Send handshake (plaintext — the connection is already TLS-protected)
    jti = None  # session_key_b64 uses the same derivation; we need jti from token
    # Re-derive the b64 key for the handshake using the same jti used in connect
    from jose import jwt as jose_jwt
    from src.apps.core import security
    from src.apps.core.config import settings
    token = websocket.query_params.get("token", "")
    try:
        payload = jose_jwt.decode(token, settings.SECRET_KEY, algorithms=[security.ALGORITHM])
        jti = payload.get("jti") or payload.get("sub", "")
    except Exception:
        jti = ""

    handshake = WSHandshakeMessage(session_key=session_key_b64(jti))
    await websocket.send_text(handshake.model_dump_json())

    if initial_room:
        await manager.join_room(user.id, initial_room)

    heartbeat_task = asyncio.create_task(_heartbeat_loop(user.id))

    try:
        while True:
            # Receive and decrypt; closes connection on decryption failure
            try:
                data = await asyncio.wait_for(
                    manager.receive_and_decrypt(websocket, user.id),
                    timeout=settings.WS_MAX_IDLE_SECONDS,
                )
            except (ValueError, RuntimeError):
                break
            except asyncio.TimeoutError:
                await manager.send_personal_model(
                    user.id,
                    WSErrorMessage(code=4008, detail="WebSocket idle timeout"),
                )
                await websocket.close(code=4008)
                break

            msg_type_raw = data.get("type", "")
            msg_id = data.get("id")

            try:
                msg_type = WSMessageType(msg_type_raw)
            except ValueError:
                await manager.send_personal_model(
                    user.id,
                    WSErrorMessage(code=4004, detail=f"Unknown message type: {msg_type_raw}"),
                )
                continue

            # ── dispatch ──────────────────────────────────────────────────

            if msg_type == WSMessageType.PING:
                await manager.send_personal_model(user.id, WSPongMessage())

            elif msg_type == WSMessageType.JOIN_ROOM:
                msg = WSJoinRoomMessage(**data)
                await manager.join_room(user.id, msg.room)
                await manager.send_personal_model(user.id, WSAckMessage(ref=msg_id))

            elif msg_type == WSMessageType.LEAVE_ROOM:
                msg = WSLeaveRoomMessage(**data)
                await manager.leave_room(user.id, msg.room)
                await manager.send_personal_model(user.id, WSAckMessage(ref=msg_id))

            elif msg_type == WSMessageType.MESSAGE:
                msg = WSMessagePayload(**data)
                out = WSRoomMessage(room=msg.room, sender_id=user.id, data=msg.data)
                await manager.broadcast_room(msg.room, out, exclude_user=user.id)
                await manager.send_personal_model(user.id, WSAckMessage(ref=msg_id))

            elif msg_type == WSMessageType.BROADCAST:
                if not user.is_superuser:
                    await manager.send_personal_model(
                        user.id,
                        WSErrorMessage(code=4030, detail="Superuser required for broadcast"),
                    )
                    continue
                msg = WSBroadcastMessage(**data)
                from src.apps.websocket.schemas.messages import WSEventMessage
                await manager.broadcast_all(WSEventMessage(event="broadcast", data=msg.data))
                await manager.send_personal_model(user.id, WSAckMessage(ref=msg_id))

            elif msg_type == WSMessageType.TYPING:
                msg = WSTypingMessage(**data)
                from src.apps.websocket.schemas.messages import WSEventMessage
                typing_event = WSEventMessage(
                    event="typing",
                    data={"user_id": encode_id(user.id), "is_typing": msg.is_typing},
                    room=msg.room,
                    sender_id=user.id,
                )
                await manager.broadcast_room(msg.room, typing_event, exclude_user=user.id)

            else:
                await manager.send_personal_model(
                    user.id,
                    WSErrorMessage(code=4005, detail=f"Unhandled message type: {msg_type}"),
                )

    except WebSocketDisconnect:
        pass
    finally:
        heartbeat_task.cancel()
        await manager.disconnect(websocket, user.id)


# ──────────────────────────────────────────────────────────────────────────────
# WebSocket endpoints
# ──────────────────────────────────────────────────────────────────────────────

@router.websocket("/")
async def ws_global(
    websocket: WebSocket,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Global WebSocket connection.

    Authenticate with ``?token=<jwt>``.  Receives personal events pushed
    by the server (e.g. notifications, payment updates).  Can join rooms
    dynamically via JOIN_ROOM messages.
    """
    await _handle_connection(websocket, db, initial_room=None)


@router.websocket("/room/{room}/")
async def ws_room(
    websocket: WebSocket,
    room: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Room-scoped WebSocket connection.

    Connects and immediately joins *room*.  Receives both room broadcasts
    and personal events.
    """
    await _handle_connection(websocket, db, initial_room=room)


# ──────────────────────────────────────────────────────────────────────────────
# REST utility endpoints
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/stats/", response_model=WSStatsResponse)
async def ws_stats(
    current_user: User = Depends(get_current_user),
) -> WSStatsResponse:
    """Return current connection statistics (authenticated users only)."""
    return WSStatsResponse(
        total_connections=manager.total_connections,
        rooms=manager.rooms_stats,
        users_online=manager.users_online,
    )


@router.get("/online/{user_id}/", response_model=WSOnlineStatusResponse)
async def ws_is_online(
    user_id: str,
    current_user: User = Depends(get_current_user),
) -> WSOnlineStatusResponse:
    """Check whether a specific user has an active WebSocket connection."""
    decoded_user_id = decode_id_or_404(user_id)
    return WSOnlineStatusResponse(
        user_id=decoded_user_id,
        online=manager.is_online(decoded_user_id),
    )
