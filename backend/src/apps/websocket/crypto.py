"""
WebSocket payload encryption — AES-256-GCM with per-session keys.

Protocol:
─────────
1. Server derives a **session key** (32 bytes) from the user's JWT *jti*
   (unique per token) and the server's SECRET_KEY using HKDF-SHA256.
2. After the WebSocket handshake the server sends a ``HANDSHAKE`` frame
   containing the session key encoded in base64.  In production this
   initial frame is sent over the already-TLS-protected connection and
   must never be forwarded to third parties.
3. From that point on every frame in **both directions** has its ``data``
   field AES-256-GCM encrypted.  The nonce is generated fresh per message
   and included alongside the ciphertext.
4. Any message that fails MAC verification is silently dropped and the
   connection is closed with code 4003.

Wire format for an encrypted frame:
    {
        "type": "<WSMessageType>",
        "iv":   "<base64 12-byte nonce>",
        "data": "<base64 AES-GCM ciphertext+tag>"
    }

Plaintext frames (sent before the handshake completes):
    HANDSHAKE, PONG, ERROR  — never carry sensitive data.
"""
import base64
import os

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from src.apps.core.config import settings


# ── Key derivation ────────────────────────────────────────────────────────────

def derive_session_key(jti: str) -> bytes:
    """
    Derive a 32-byte AES session key from the token's JTI.

    Using HKDF-SHA256 with the server SECRET_KEY as the salt means:
      • Each token (jti) gets a unique session key.
      • Rotating SECRET_KEY invalidates all existing session keys.
      • The key cannot be guessed without the server secret.
    """
    return HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=settings.SECRET_KEY.encode(),
        info=b"ws-session-key:" + jti.encode(),
    ).derive(jti.encode())


def session_key_b64(jti: str) -> str:
    """Return the session key as a base64 string (safe to send over the wire)."""
    return base64.b64encode(derive_session_key(jti)).decode()


# ── Symmetric AES-256-GCM helpers ────────────────────────────────────────────

def encrypt(plaintext: bytes, key: bytes) -> tuple[str, str]:
    """
    Encrypt *plaintext* with *key* (32 bytes, AES-256-GCM).

    Returns ``(iv_b64, ciphertext_b64)`` where ciphertext includes the
    16-byte GCM authentication tag appended by the ``cryptography`` library.
    """
    iv = os.urandom(12)
    ct = AESGCM(key).encrypt(iv, plaintext, None)
    return base64.b64encode(iv).decode(), base64.b64encode(ct).decode()


def decrypt(iv_b64: str, ciphertext_b64: str, key: bytes) -> bytes:
    """
    Decrypt and verify an AES-256-GCM ciphertext.

    Raises ``cryptography.exceptions.InvalidTag`` if authentication fails
    (tampered or wrong key) — caller should close the connection.
    """
    iv = base64.b64decode(iv_b64)
    ct = base64.b64decode(ciphertext_b64)
    return AESGCM(key).decrypt(iv, ct, None)
