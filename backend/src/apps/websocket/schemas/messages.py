"""
WebSocket message schemas.

All messages are JSON with a ``type`` discriminator field.  The server
always echoes ``timestamp`` back so clients can measure latency.

Encryption
──────────
Every frame after the initial HANDSHAKE is wrapped in ``WSEncryptedFrame``:
    {
        "type": "<message type string>",
        "iv":   "<base64 12-byte nonce>",
        "data": "<base64 AES-256-GCM ciphertext>"
    }
The plaintext inside ``data`` is the JSON of the actual message model.
The HANDSHAKE frame itself is sent in plaintext (over TLS) and carries
the per-session AES key the client must use for all subsequent frames.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, field_serializer

from src.apps.iam.utils.hashid import encode_id


class WSMessageType(str, Enum):
    # ── handshake ─────────────────────────────────────────
    HANDSHAKE  = "handshake"

    # ── client → server ────────────────────────────────────
    PING       = "ping"
    JOIN_ROOM  = "join_room"
    LEAVE_ROOM = "leave_room"
    MESSAGE    = "message"
    BROADCAST  = "broadcast"   # superuser only
    TYPING     = "typing"

    # ── server → client ────────────────────────────────────
    PONG       = "pong"
    ACK        = "ack"
    ERROR      = "error"
    PRESENCE   = "presence"
    SYSTEM     = "system"
    EVENT      = "event"


# ──────────────────────────────────────────────────────────
# Encrypted frame envelope
# ──────────────────────────────────────────────────────────

class WSEncryptedFrame(BaseModel):
    """
    Wrapper for every WebSocket frame after the handshake.

    The plaintext (encrypted into ``data``) is the JSON string of the
    actual message model.  ``type`` is kept plaintext so the receiver
    knows how to route/log before decrypting.
    """
    type: str   # plaintext message type discriminator
    iv: str     # base64 12-byte AES-GCM nonce
    data: str   # base64 AES-256-GCM ciphertext (includes 16-byte auth tag)


class WSHandshakeMessage(BaseModel):
    """
    First frame sent by the server after accepting the connection (plaintext,
    over TLS).  The client stores ``session_key`` and uses it to
    encrypt/decrypt all subsequent frames.
    """
    type: WSMessageType = WSMessageType.HANDSHAKE
    session_key: str    # base64 32-byte AES-256-GCM session key


# ──────────────────────────────────────────────────────────
# Inbound  (client → server)
# ──────────────────────────────────────────────────────────

class WSInboundMessage(BaseModel):
    """All client messages must carry a ``type`` field."""
    type: WSMessageType
    # Optional client-side message id — echoed back in ACK
    id: Optional[str] = None


class WSPingMessage(WSInboundMessage):
    type: WSMessageType = WSMessageType.PING


class WSJoinRoomMessage(WSInboundMessage):
    type: WSMessageType = WSMessageType.JOIN_ROOM
    room: str


class WSLeaveRoomMessage(WSInboundMessage):
    type: WSMessageType = WSMessageType.LEAVE_ROOM
    room: str


class WSMessagePayload(WSInboundMessage):
    """Generic message to a room."""
    type: WSMessageType = WSMessageType.MESSAGE
    room: str
    data: Any   # any JSON-serialisable payload


class WSBroadcastMessage(WSInboundMessage):
    """Superuser broadcast to all connected clients."""
    type: WSMessageType = WSMessageType.BROADCAST
    data: Any


class WSTypingMessage(WSInboundMessage):
    type: WSMessageType = WSMessageType.TYPING
    room: str
    is_typing: bool = True


# ──────────────────────────────────────────────────────────
# Outbound  (server → client)
# ──────────────────────────────────────────────────────────

def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class WSOutboundMessage(BaseModel):
    type: WSMessageType
    timestamp: str = ""

    def model_post_init(self, __context: Any) -> None:
        if not self.timestamp:
            self.timestamp = _utcnow()


class WSPongMessage(WSOutboundMessage):
    type: WSMessageType = WSMessageType.PONG


class WSAckMessage(WSOutboundMessage):
    type: WSMessageType = WSMessageType.ACK
    ref: Optional[str] = None   # echoes back ``id`` from the inbound message


class WSErrorMessage(WSOutboundMessage):
    type: WSMessageType = WSMessageType.ERROR
    code: int
    detail: str


class WSPresenceMessage(WSOutboundMessage):
    """Broadcast when a user joins or leaves a room."""
    type: WSMessageType = WSMessageType.PRESENCE
    room: str
    user_id: int
    online: bool

    @field_serializer("user_id")
    def serialize_user_id(self, value: int) -> str:
        return encode_id(value)


class WSSystemMessage(WSOutboundMessage):
    """Arbitrary server-initiated text notification."""
    type: WSMessageType = WSMessageType.SYSTEM
    text: str


class WSEventMessage(WSOutboundMessage):
    """
    Generic server-push event.  Use ``event`` to categorise
    (e.g. "payment.completed", "order.updated") and ``data`` for the payload.
    This is the primary hook for integrating real-time updates from other
    parts of the application (finance, IAM, etc.).
    """
    type: WSMessageType = WSMessageType.EVENT
    event: str
    data: Any
    room: Optional[str] = None      # None → personal delivery
    sender_id: Optional[int] = None

    @field_serializer("sender_id")
    def serialize_sender_id(self, value: int | None) -> str | None:
        if value is None:
            return None
        return encode_id(value)


class WSRoomMessage(WSOutboundMessage):
    """Relayed room message."""
    type: WSMessageType = WSMessageType.MESSAGE
    room: str
    sender_id: int
    data: Any

    @field_serializer("sender_id")
    def serialize_sender_id(self, value: int) -> str:
        return encode_id(value)


# ──────────────────────────────────────────────────────────
# REST schemas
# ──────────────────────────────────────────────────────────

class WSStatsResponse(BaseModel):
    total_connections: int
    rooms: dict[str, int]   # room_name → active member count
    users_online: list[int]  # list of user_ids currently connected

    @field_serializer("users_online")
    def serialize_users_online(self, value: list[int]) -> list[str]:
        return [encode_id(user_id) for user_id in value]


class WSOnlineStatusResponse(BaseModel):
    user_id: int
    online: bool

    @field_serializer("user_id")
    def serialize_user_id(self, value: int) -> str:
        return encode_id(value)
