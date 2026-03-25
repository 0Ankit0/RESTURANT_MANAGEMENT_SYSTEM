"""
Unit tests for the WebSocket module.

Covers:
  - crypto: AES-256-GCM encrypt/decrypt, session key derivation
  - manager: connect/disconnect, room join/leave, send_personal, broadcast
  - auth dep: valid token accepted, invalid/missing rejected
  - routes: WS handshake + message exchange, REST /stats/, /online/
  - encryption: every frame after handshake is an encrypted WSEncryptedFrame
"""
import base64
import json
import pytest
from unittest.mock import AsyncMock, MagicMock

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.core import security
from src.apps.core.security import TokenType
from src.apps.iam.models.token_tracking import TokenTracking
from src.apps.websocket.crypto import (
    decrypt,
    derive_session_key,
    encrypt,
    session_key_b64,
)
from src.apps.websocket.manager import ConnectionManager
from src.apps.websocket.schemas.messages import (
    WSEncryptedFrame,
    WSEventMessage,
    WSHandshakeMessage,  # noqa: F401 — used in handshake assertions
    WSMessageType,       # noqa: F401 — used by schema models
    WSPongMessage,
    WSSystemMessage,     # noqa: F401 — exported for consumer convenience
)
from tests.factories import UserFactory


# ──────────────────────────────────────────────────────────────────────────────
# Crypto unit tests
# ──────────────────────────────────────────────────────────────────────────────

class TestCrypto:
    @pytest.mark.unit
    def test_encrypt_decrypt_roundtrip(self):
        key = derive_session_key("test-jti-123")
        plaintext = b'{"type":"ping"}'
        iv_b64, ct_b64 = encrypt(plaintext, key)
        assert iv_b64 != ""
        assert ct_b64 != ""
        recovered = decrypt(iv_b64, ct_b64, key)
        assert recovered == plaintext

    @pytest.mark.unit
    def test_different_keys_fail_decrypt(self):
        key1 = derive_session_key("jti-aaa")
        key2 = derive_session_key("jti-bbb")
        iv_b64, ct_b64 = encrypt(b"secret", key1)
        from cryptography.exceptions import InvalidTag
        with pytest.raises(InvalidTag):
            decrypt(iv_b64, ct_b64, key2)

    @pytest.mark.unit
    def test_session_key_deterministic(self):
        k1 = derive_session_key("fixed-jti")
        k2 = derive_session_key("fixed-jti")
        assert k1 == k2

    @pytest.mark.unit
    def test_session_key_unique_per_jti(self):
        assert derive_session_key("jti-x") != derive_session_key("jti-y")

    @pytest.mark.unit
    def test_session_key_b64_is_32_bytes(self):
        b64 = session_key_b64("any-jti")
        raw = base64.b64decode(b64)
        assert len(raw) == 32

    @pytest.mark.unit
    def test_encrypt_nonce_is_unique(self):
        """Each encrypt call produces a fresh nonce."""
        key = derive_session_key("jti-nonce-test")
        iv1, _ = encrypt(b"hello", key)
        iv2, _ = encrypt(b"hello", key)
        assert iv1 != iv2


# ──────────────────────────────────────────────────────────────────────────────
# ConnectionManager unit tests
# ──────────────────────────────────────────────────────────────────────────────

class TestConnectionManager:
    def _make_ws(self) -> MagicMock:
        ws = MagicMock()
        ws.send_text = AsyncMock()
        ws.accept = AsyncMock()
        return ws

    def _make_key(self) -> bytes:
        return derive_session_key("test-jti")

    @pytest.mark.unit
    async def test_connect_increments_count(self):
        mgr = ConnectionManager()
        ws = self._make_ws()
        await mgr.connect(ws, user_id=1, session_key=self._make_key())
        assert mgr.total_connections == 1
        assert mgr.is_online(1)

    @pytest.mark.unit
    async def test_disconnect_removes_user(self):
        mgr = ConnectionManager()
        ws = self._make_ws()
        key = self._make_key()
        await mgr.connect(ws, user_id=1, session_key=key)
        await mgr.disconnect(ws, user_id=1)
        assert not mgr.is_online(1)
        assert mgr.total_connections == 0

    @pytest.mark.unit
    async def test_join_leave_room(self):
        mgr = ConnectionManager()
        ws = self._make_ws()
        key = self._make_key()
        await mgr.connect(ws, user_id=1, session_key=key)
        await mgr.join_room(1, "lobby")
        assert "lobby" in mgr.rooms_stats
        assert mgr.rooms_stats["lobby"] == 1
        await mgr.leave_room(1, "lobby")
        assert "lobby" not in mgr.rooms_stats

    @pytest.mark.unit
    async def test_send_personal_encrypts_frame(self):
        mgr = ConnectionManager()
        ws = self._make_ws()
        key = self._make_key()
        await mgr.connect(ws, user_id=1, session_key=key)

        msg = WSPongMessage()
        await mgr.send_personal_model(1, msg)

        ws.send_text.assert_called_once()
        raw = ws.send_text.call_args[0][0]
        frame = WSEncryptedFrame.model_validate_json(raw)
        # Decrypt and verify the inner message
        plaintext = decrypt(frame.iv, frame.data, key)
        inner = json.loads(plaintext)
        assert inner["type"] == "pong"

    @pytest.mark.unit
    async def test_broadcast_room_sends_to_all_members(self):
        mgr = ConnectionManager()
        ws1 = self._make_ws()
        ws2 = self._make_ws()
        k1 = derive_session_key("jti-1")
        k2 = derive_session_key("jti-2")
        await mgr.connect(ws1, 1, k1)
        await mgr.connect(ws2, 2, k2)
        await mgr.join_room(1, "room-a")
        await mgr.join_room(2, "room-a")

        # Reset after join presence broadcasts
        ws1.send_text.reset_mock()
        ws2.send_text.reset_mock()

        event = WSEventMessage(event="test.event", data={"x": 1})
        await mgr.broadcast_room("room-a", event)

        ws1.send_text.assert_called_once()
        ws2.send_text.assert_called_once()

        # Verify both frames decrypt correctly
        for ws, key in [(ws1, k1), (ws2, k2)]:
            raw = ws.send_text.call_args[0][0]
            frame = WSEncryptedFrame.model_validate_json(raw)
            inner = json.loads(decrypt(frame.iv, frame.data, key))
            assert inner["event"] == "test.event"

    @pytest.mark.unit
    async def test_broadcast_room_exclude_sender(self):
        mgr = ConnectionManager()
        ws1 = self._make_ws()
        ws2 = self._make_ws()
        k1 = derive_session_key("jti-ex-1")
        k2 = derive_session_key("jti-ex-2")
        await mgr.connect(ws1, 1, k1)
        await mgr.connect(ws2, 2, k2)
        await mgr.join_room(1, "room-b")
        await mgr.join_room(2, "room-b")
        ws1.send_text.reset_mock()
        ws2.send_text.reset_mock()

        event = WSEventMessage(event="msg", data={})
        await mgr.broadcast_room("room-b", event, exclude_user=1)

        ws1.send_text.assert_not_called()
        ws2.send_text.assert_called_once()

    @pytest.mark.unit
    async def test_users_online_list(self):
        mgr = ConnectionManager()
        ws1 = self._make_ws()
        ws2 = self._make_ws()
        await mgr.connect(ws1, 10, derive_session_key("j10"))
        await mgr.connect(ws2, 20, derive_session_key("j20"))
        assert set(mgr.users_online) == {10, 20}

    @pytest.mark.unit
    async def test_disconnect_removes_from_rooms(self):
        mgr = ConnectionManager()
        ws = self._make_ws()
        key = derive_session_key("jti-rm")
        await mgr.connect(ws, 5, key)
        await mgr.join_room(5, "room-cleanup")
        assert mgr.rooms_stats.get("room-cleanup") == 1
        await mgr.disconnect(ws, 5)
        assert "room-cleanup" not in mgr.rooms_stats

    @pytest.mark.unit
    async def test_push_event_helper(self):
        mgr = ConnectionManager()
        ws = self._make_ws()
        key = derive_session_key("jti-push")
        await mgr.connect(ws, 7, key)
        await mgr.push_event(7, "payment.completed", {"amount": 100})
        ws.send_text.assert_called_once()
        frame = WSEncryptedFrame.model_validate_json(ws.send_text.call_args[0][0])
        inner = json.loads(decrypt(frame.iv, frame.data, key))
        assert inner["type"] == "event"
        assert inner["event"] == "payment.completed"


# ──────────────────────────────────────────────────────────────────────────────
# REST endpoint tests
# ──────────────────────────────────────────────────────────────────────────────

class TestWSRestEndpoints:
    async def _make_auth_user(self, db_session: AsyncSession):
        user = UserFactory.build(
            username="wsuser",
            email="ws@example.com",
            hashed_password=security.get_password_hash("Pass123!"),
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    async def _get_token(self, client: AsyncClient, db_session: AsyncSession):
        user = await self._make_auth_user(db_session)
        resp = await client.post(
            "/api/v1/auth/login/?set_cookie=false",
            json={"username": "wsuser", "password": "Pass123!"},
        )
        return resp.json().get("access", ""), user

    @pytest.mark.unit
    async def test_stats_requires_auth(self, client: AsyncClient):
        resp = await client.get("/api/v1/ws/stats/")
        assert resp.status_code == 401

    @pytest.mark.unit
    async def test_online_requires_auth(self, client: AsyncClient):
        resp = await client.get("/api/v1/ws/online/1/")
        assert resp.status_code == 401

    @pytest.mark.unit
    async def test_stats_returns_structure(self, client: AsyncClient, db_session: AsyncSession):
        token, _ = await self._get_token(client, db_session)
        resp = await client.get(
            "/api/v1/ws/stats/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "total_connections" in data
        assert "rooms" in data
        assert "users_online" in data

    @pytest.mark.unit
    async def test_online_check(self, client: AsyncClient, db_session: AsyncSession):
        token, user = await self._get_token(client, db_session)
        resp = await client.get(
            f"/api/v1/ws/online/{user.id}/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["user_id"] == user.id
        assert data["online"] is False  # not connected via WS in this test


# ──────────────────────────────────────────────────────────────────────────────
# Handshake + message flow tests (using mock WebSocket)
# ──────────────────────────────────────────────────────────────────────────────

class TestWSHandshakeAndMessages:
    """
    Test the WebSocket message loop by calling the handler directly with
    a mock WebSocket and a real DB session.
    """

    async def _setup_user_and_token(self, db_session: AsyncSession):
        from datetime import datetime, timedelta, timezone
        from jose import jwt
        from src.apps.core.config import settings
        from src.apps.core.security import ALGORITHM
        import uuid

        user = UserFactory.build(
            username="wshandshake",
            email="wshandshake@example.com",
            hashed_password=security.get_password_hash("Pass123!"),
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        jti = str(uuid.uuid4())
        expires = datetime.now(timezone.utc) + timedelta(hours=1)
        token = jwt.encode(
            {"sub": str(user.id), "jti": jti, "exp": expires, "type": "access"},
            settings.SECRET_KEY,
            algorithm=ALGORITHM,
        )

        # Register token in tracking table
        tracking = TokenTracking(
            user_id=user.id,
            token_jti=jti,
            token_type=TokenType.ACCESS,
            ip_address="127.0.0.1",
            user_agent="test",
            expires_at=expires,
            is_active=True,
        )
        db_session.add(tracking)

        await db_session.commit()
        return user, token, jti

    def _make_mock_ws(self, token: str, texts_to_receive: list[str]) -> MagicMock:
        ws = MagicMock()
        ws.accept = AsyncMock()
        ws.close = AsyncMock()
        ws.send_text = AsyncMock()
        ws.query_params = {"token": token}

        from fastapi.websockets import WebSocketDisconnect
        receive_calls = iter(texts_to_receive)

        async def _recv():
            try:
                return next(receive_calls)
            except StopIteration:
                raise WebSocketDisconnect()

        ws.receive_text = _recv
        return ws

    def _make_encrypted_frame(self, jti: str, payload: dict) -> str:
        """Encrypt a client-side message frame using the session key."""
        key = derive_session_key(jti)
        plaintext = json.dumps(payload).encode()
        iv_b64, ct_b64 = encrypt(plaintext, key)
        return WSEncryptedFrame(type=payload["type"], iv=iv_b64, data=ct_b64).model_dump_json()

    @pytest.mark.unit
    async def test_handshake_frame_sent_on_connect(self, db_session: AsyncSession):
        """Server sends a HANDSHAKE frame with the session key on connect."""
        user, token, _jti = await self._setup_user_and_token(db_session)
        ws = self._make_mock_ws(token, [])  # no messages — disconnect immediately

        from src.apps.websocket.api.v1.ws import _handle_connection
        await _handle_connection(ws, db_session, initial_room=None)

        ws.accept.assert_called_once()
        # First send_text call must be the HANDSHAKE
        first_call = ws.send_text.call_args_list[0][0][0]
        handshake = json.loads(first_call)
        assert handshake["type"] == "handshake"
        assert "session_key" in handshake
        # Verify the key is 32 bytes
        assert len(base64.b64decode(handshake["session_key"])) == 32

    @pytest.mark.unit
    async def test_ping_returns_encrypted_pong(self, db_session: AsyncSession):
        """PING message should yield an encrypted PONG frame."""
        _user, token, jti = await self._setup_user_and_token(db_session)

        ping_frame = self._make_encrypted_frame(jti, {"type": "ping"})
        ws = self._make_mock_ws(token, [ping_frame])

        from src.apps.websocket.api.v1.ws import _handle_connection
        await _handle_connection(ws, db_session, initial_room=None)

        # Find the PONG call (after the handshake)
        calls = [c[0][0] for c in ws.send_text.call_args_list]
        pong_frames = []
        key = derive_session_key(jti)
        for raw in calls[1:]:  # skip handshake
            try:
                frame = WSEncryptedFrame.model_validate_json(raw)
                inner = json.loads(decrypt(frame.iv, frame.data, key))
                if inner.get("type") == "pong":
                    pong_frames.append(inner)
            except Exception:
                continue

        assert len(pong_frames) == 1

    @pytest.mark.unit
    async def test_invalid_token_closes_with_4001(self, db_session: AsyncSession):
        """Connecting with a bad token should close with code 4001."""
        ws = MagicMock()
        ws.accept = AsyncMock()
        ws.close = AsyncMock()
        ws.send_json = AsyncMock()
        ws.send_text = AsyncMock()
        ws.query_params = {"token": "invalid.jwt.token"}

        from src.apps.websocket.api.v1.ws import _handle_connection
        await _handle_connection(ws, db_session, initial_room=None)

        ws.close.assert_called_once_with(code=4001)

    @pytest.mark.unit
    async def test_missing_token_closes_with_4001(self, db_session: AsyncSession):
        """Connecting without a token should close with code 4001."""
        ws = MagicMock()
        ws.accept = AsyncMock()
        ws.close = AsyncMock()
        ws.send_json = AsyncMock()
        ws.send_text = AsyncMock()
        ws.query_params = {}

        from src.apps.websocket.api.v1.ws import _handle_connection
        await _handle_connection(ws, db_session, initial_room=None)

        ws.close.assert_called_once_with(code=4001)
