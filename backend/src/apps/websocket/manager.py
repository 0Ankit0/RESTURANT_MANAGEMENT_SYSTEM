"""
ConnectionManager — manages all active WebSocket connections.

Every outbound message is AES-256-GCM encrypted with the per-session key
before being sent.  Incoming frames are decrypted before dispatch.
The session key is derived from the user's JWT jti via HKDF (see crypto.py).

Features
────────
• Per-user multi-connection tracking (same user on multiple tabs/devices)
• Named rooms with join / leave
• Broadcast to a room, to a specific user, or to all connections
• Redis pub/sub fan-out (optional, used when not DEBUG and REDIS_URL set)
  so multiple server instances can deliver messages to any user.
• push_event() / push_event_to_room() for REST handlers and background tasks.

Usage from application code
────────────────────────────
    from src.apps.websocket.manager import manager

    # push to one user
    await manager.push_event(user_id=42, event="payment.completed", data={...})

    # push to everyone in a room
    await manager.push_event_to_room("orders", "order.updated", data={...})
"""
import asyncio
import json
import logging
from collections import defaultdict
from typing import Any, Optional

from fastapi import WebSocket

from src.apps.websocket.crypto import decrypt, encrypt
from src.apps.websocket.schemas.messages import (
    WSEncryptedFrame,
    WSErrorMessage,
    WSEventMessage,
    WSPresenceMessage,
    WSSystemMessage,
)

log = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self) -> None:
        # user_id → {websocket: session_key_bytes}
        self._user_connections: dict[int, dict[WebSocket, bytes]] = defaultdict(dict)
        # room → set of user_ids
        self._rooms: dict[str, set[int]] = defaultdict(set)
        self._redis: Any = None
        self._pubsub_task: Optional[asyncio.Task] = None

    # ── connection lifecycle ──────────────────────────────────────────────

    async def connect(self, websocket: WebSocket, user_id: int, session_key: bytes) -> None:
        await websocket.accept()
        self._user_connections[user_id][websocket] = session_key
        log.debug("WS connect  user=%s  total=%s", user_id, self.total_connections)

    async def disconnect(self, websocket: WebSocket, user_id: int) -> None:
        self._user_connections[user_id].pop(websocket, None)
        if not self._user_connections[user_id]:
            del self._user_connections[user_id]

        for room, members in list(self._rooms.items()):
            if user_id in members:
                members.discard(user_id)
                if not members:
                    del self._rooms[room]
                else:
                    await self._broadcast_room_json(
                        room,
                        WSPresenceMessage(room=room, user_id=user_id, online=False),
                    )
        log.debug("WS disconnect user=%s  remaining=%s", user_id, self.total_connections)

    # ── room management ───────────────────────────────────────────────────

    async def join_room(self, user_id: int, room: str) -> None:
        self._rooms[room].add(user_id)
        await self._broadcast_room_json(
            room,
            WSPresenceMessage(room=room, user_id=user_id, online=True),
        )

    async def leave_room(self, user_id: int, room: str) -> None:
        self._rooms[room].discard(user_id)
        if not self._rooms[room]:
            del self._rooms[room]
        await self._broadcast_room_json(
            room,
            WSPresenceMessage(room=room, user_id=user_id, online=False),
        )

    # ── encrypted send helpers ────────────────────────────────────────────

    def _make_frame(self, msg_type: str, payload_json: str, key: bytes) -> str:
        """Encrypt *payload_json* and return a ``WSEncryptedFrame`` JSON string."""
        iv_b64, ct_b64 = encrypt(payload_json.encode(), key)
        return WSEncryptedFrame(type=msg_type, iv=iv_b64, data=ct_b64).model_dump_json()

    async def send_personal_model(self, user_id: int, message: Any) -> None:
        """Encrypt and deliver a Pydantic message model to all connections of a user."""
        payload = message.model_dump_json()
        msg_type = message.type.value if hasattr(message.type, "value") else str(message.type)
        dead: list[WebSocket] = []
        for ws, key in list(self._user_connections.get(user_id, {}).items()):
            try:
                await ws.send_text(self._make_frame(msg_type, payload, key))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._user_connections[user_id].pop(ws, None)

    async def send_personal_raw(self, user_id: int, msg_type: str, payload_json: str) -> None:
        """Encrypt a raw JSON payload and deliver to all connections of a user."""
        dead: list[WebSocket] = []
        for ws, key in list(self._user_connections.get(user_id, {}).items()):
            try:
                await ws.send_text(self._make_frame(msg_type, payload_json, key))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._user_connections[user_id].pop(ws, None)

    async def _broadcast_room_json(
        self,
        room: str,
        message: Any,
        exclude_user: Optional[int] = None,
    ) -> None:
        payload = message.model_dump_json()
        msg_type = message.type.value if hasattr(message.type, "value") else str(message.type)
        for uid in list(self._rooms.get(room, [])):
            if uid == exclude_user:
                continue
            await self.send_personal_raw(uid, msg_type, payload)

    async def broadcast_room(self, room: str, message: Any, exclude_user: Optional[int] = None) -> None:
        await self._broadcast_room_json(room, message, exclude_user)

    async def broadcast_all(self, message: Any) -> None:
        payload = message.model_dump_json()
        msg_type = message.type.value if hasattr(message.type, "value") else str(message.type)
        for uid in list(self._user_connections):
            await self.send_personal_raw(uid, msg_type, payload)

    # ── receive / decrypt helper ──────────────────────────────────────────

    async def receive_and_decrypt(self, websocket: WebSocket, user_id: int) -> dict:
        """
        Receive the next frame from *websocket*, decrypt it, and return
        the parsed JSON dict of the inner plaintext message.

        Closes the connection with code 4003 on decryption failure.
        """
        raw = await websocket.receive_text()
        key = self._user_connections.get(user_id, {}).get(websocket)
        if key is None:
            await websocket.close(code=4001)
            raise ValueError("No session key for connection")

        try:
            frame = WSEncryptedFrame.model_validate_json(raw)
            plaintext = decrypt(frame.iv, frame.data, key)
            return json.loads(plaintext)
        except Exception as exc:
            log.warning("WS decrypt failed user=%s: %s", user_id, exc)
            err = WSErrorMessage(code=4003, detail="Message decryption failed")
            # Send error unencrypted so client can read it before close
            await websocket.send_text(err.model_dump_json())
            await websocket.close(code=4003)
            raise

    # ── high-level push helpers (for use from REST handlers / tasks) ──────

    async def push_event(self, user_id: int, event: str, data: Any) -> None:
        """Push a typed EVENT to a specific connected user."""
        await self.send_personal_model(user_id, WSEventMessage(event=event, data=data))

    async def push_event_to_room(
        self,
        room: str,
        event: str,
        data: Any,
        sender_id: Optional[int] = None,
        exclude_user: Optional[int] = None,
    ) -> None:
        """Push a typed EVENT to all members of a room."""
        msg = WSEventMessage(event=event, data=data, room=room, sender_id=sender_id)
        await self.broadcast_room(room, msg, exclude_user=exclude_user)

    async def push_system(self, user_id: int, text: str) -> None:
        await self.send_personal_model(user_id, WSSystemMessage(text=text))

    # ── stats ─────────────────────────────────────────────────────────────

    @property
    def total_connections(self) -> int:
        return sum(len(v) for v in self._user_connections.values())

    @property
    def rooms_stats(self) -> dict[str, int]:
        return {room: len(members) for room, members in self._rooms.items()}

    @property
    def users_online(self) -> list[int]:
        return list(self._user_connections.keys())

    def is_online(self, user_id: int) -> bool:
        return user_id in self._user_connections

    # ── optional Redis pub/sub (multi-instance) ───────────────────────────

    async def setup_redis(self, redis_url: str) -> None:
        """
        Set up Redis pub/sub for multi-instance deployments.
        Payloads published via Redis are already-encrypted frames (the
        session key is per-user-connection, not shared cross-instance),
        so only broadcast_all and room events are forwarded through Redis.
        """
        try:
            import redis.asyncio as aioredis
            self._redis = await aioredis.from_url(redis_url, decode_responses=True)
            pubsub = self._redis.pubsub()
            await pubsub.subscribe("ws:events")
            self._pubsub_task = asyncio.create_task(self._redis_listener(pubsub))
            log.info("WebSocket Redis pub/sub initialised")
        except Exception as exc:
            log.warning("WebSocket Redis setup skipped (single-instance mode): %s", exc)

    async def _redis_listener(self, pubsub: Any) -> None:
        async for msg in pubsub.listen():
            if msg["type"] == "message":
                try:
                    payload = json.loads(msg["data"])
                    if payload.get("target") == "room":
                        event_msg = WSEventMessage(**payload["message"])
                        await self._broadcast_room_json(payload["room"], event_msg)
                except Exception as exc:
                    log.warning("Redis ws message error: %s", exc)

    async def teardown(self) -> None:
        if self._pubsub_task:
            self._pubsub_task.cancel()
        if self._redis:
            await self._redis.aclose()


# Module-level singleton — imported by routes and the rest of the app
manager = ConnectionManager()
