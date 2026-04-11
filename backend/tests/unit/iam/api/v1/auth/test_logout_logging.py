import logging
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import Response
from starlette.requests import Request

from src.apps.iam.api.v1.auth import login as login_module


@pytest.mark.asyncio
async def test_logout_logs_token_revocation_failure(monkeypatch, caplog):
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/v1/auth/logout/",
        "headers": [(b"authorization", b"Bearer token123")],
        "client": ("127.0.0.1", 12345),
    }
    request = Request(scope)
    response = Response()
    current_user = SimpleNamespace(id=42)
    db = AsyncMock()
    db.execute.return_value.scalars.return_value.all.return_value = []
    analytics = SimpleNamespace(capture=AsyncMock())

    monkeypatch.setattr(login_module, "get_client_ip", lambda _request: "127.0.0.1")
    monkeypatch.setattr(login_module.jwt, "decode", Mock(side_effect=RuntimeError("bad token")))

    with caplog.at_level(logging.ERROR):
        payload = await login_module.logout(
            request=request,
            response=response,
            current_user=current_user,
            db=db,
            analytics=analytics,
        )

    assert payload == {"message": "Successfully logged out from this device"}
    assert "auth.logout.token_revocation_failed" in caplog.text
    assert any(getattr(record, "user_id", None) == 42 for record in caplog.records)
