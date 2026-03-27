import pytest
from fastapi import HTTPException
from starlette.requests import Request

from src.apps.restaurant.access.control import require_restaurant_access


class _State:
    json_body = None


def _request(method: str = "GET", path: str = "/api/v1/branches/1/tables", headers: dict[str, str] | None = None, query: str = "") -> Request:
    scope = {
        "type": "http",
        "method": method,
        "path": path,
        "headers": [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()],
        "query_string": query.encode(),
        "path_params": {"branch_id": "1"},
    }
    req = Request(scope)
    req.state = _State()
    return req


@pytest.mark.asyncio
async def test_missing_role_header_rejected(monkeypatch):
    monkeypatch.setattr("src.apps.restaurant.access.control.settings.TESTING", False)
    request = _request(headers={"X-Branch-Id": "1"})

    with pytest.raises(HTTPException) as exc:
        await require_restaurant_access(request)

    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_branch_scope_mismatch_rejected(monkeypatch):
    monkeypatch.setattr("src.apps.restaurant.access.control.settings.TESTING", False)
    request = _request(headers={"X-Restaurant-Role": "waiter", "X-Branch-Id": "2"})

    with pytest.raises(HTTPException) as exc:
        await require_restaurant_access(request)

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_admin_cross_branch_allowed(monkeypatch):
    monkeypatch.setattr("src.apps.restaurant.access.control.settings.TESTING", False)
    request = _request(headers={"X-Restaurant-Role": "admin"})

    await require_restaurant_access(request)
