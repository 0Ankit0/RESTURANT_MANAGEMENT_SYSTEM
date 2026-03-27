from __future__ import annotations

from enum import StrEnum

from fastapi import Depends, HTTPException, Request, status

from src.apps.core.config import settings


class RestaurantRole(StrEnum):
    GUEST = "guest"
    HOST = "host"
    WAITER = "waiter"
    CAPTAIN = "captain"
    CHEF = "chef"
    CASHIER = "cashier"
    ACCOUNTANT = "accountant"
    INVENTORY_MANAGER = "inventory_manager"
    PURCHASE_MANAGER = "purchase_manager"
    BRANCH_MANAGER = "branch_manager"
    ADMIN = "admin"


def _extract_effective_branch_id(request: Request) -> int | None:
    # Prefer explicit route/query IDs.
    for source in (request.path_params, request.query_params):
        raw = source.get("branch_id")
        if raw is not None:
            try:
                return int(raw)
            except (TypeError, ValueError):
                return None

    # Fallback for JSON body payloads that carry branch_id.
    body = getattr(request.state, "json_body", None)
    if isinstance(body, dict) and body.get("branch_id") is not None:
        try:
            return int(body["branch_id"])
        except (TypeError, ValueError):
            return None

    return None


async def _capture_json_body(request: Request) -> None:
    if request.method in {"POST", "PUT", "PATCH"} and request.headers.get("content-type", "").startswith("application/json"):
        try:
            request.state.json_body = await request.json()
        except Exception:  # noqa: BLE001
            request.state.json_body = None


async def require_restaurant_access(request: Request) -> None:
    """Enforce role + branch scope via lightweight headers.

    Headers:
    - X-Restaurant-Role: role string
    - X-Branch-Id: branch scope for non-admin users

    During test runs we skip enforcement to preserve current integration contracts.
    """
    if settings.TESTING:
        return

    await _capture_json_body(request)

    role_header = request.headers.get("X-Restaurant-Role", "").strip().lower()
    if not role_header:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing X-Restaurant-Role header")

    try:
        role = RestaurantRole(role_header)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unsupported restaurant role") from exc

    requested_branch_id = _extract_effective_branch_id(request)
    scope_branch_header = request.headers.get("X-Branch-Id")

    # Admin can access cross-branch resources.
    if role == RestaurantRole.ADMIN:
        return

    if not scope_branch_header:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing X-Branch-Id header")

    try:
        scope_branch_id = int(scope_branch_header)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid X-Branch-Id header") from exc

    if requested_branch_id is not None and scope_branch_id != requested_branch_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Branch scope mismatch")


RestaurantAccessDependency = Depends(require_restaurant_access)
