"""Access domain utilities for branch-scoped RBAC and privileged actions."""

from __future__ import annotations

from enum import StrEnum


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


BRANCH_SCOPED_ROLES: set[RestaurantRole] = {
    RestaurantRole.HOST,
    RestaurantRole.WAITER,
    RestaurantRole.CAPTAIN,
    RestaurantRole.CHEF,
    RestaurantRole.CASHIER,
    RestaurantRole.INVENTORY_MANAGER,
    RestaurantRole.PURCHASE_MANAGER,
    RestaurantRole.BRANCH_MANAGER,
}

ORG_WIDE_ROLES: set[RestaurantRole] = {
    RestaurantRole.ADMIN,
    RestaurantRole.ACCOUNTANT,
}

_ACTION_PERMISSIONS: dict[str, set[RestaurantRole]] = {
    "branch.bootstrap": {RestaurantRole.ADMIN, RestaurantRole.BRANCH_MANAGER},
    "branch.configure": {RestaurantRole.ADMIN, RestaurantRole.BRANCH_MANAGER},
    "tables.manage": {RestaurantRole.ADMIN, RestaurantRole.BRANCH_MANAGER, RestaurantRole.HOST},
    "reservation.manage": {RestaurantRole.ADMIN, RestaurantRole.BRANCH_MANAGER, RestaurantRole.HOST},
    "waitlist.manage": {RestaurantRole.ADMIN, RestaurantRole.BRANCH_MANAGER, RestaurantRole.HOST},
    "orders.manage": {RestaurantRole.ADMIN, RestaurantRole.BRANCH_MANAGER, RestaurantRole.WAITER, RestaurantRole.CAPTAIN},
    "kitchen.manage": {RestaurantRole.ADMIN, RestaurantRole.BRANCH_MANAGER, RestaurantRole.CHEF},
    "inventory.manage": {RestaurantRole.ADMIN, RestaurantRole.BRANCH_MANAGER, RestaurantRole.INVENTORY_MANAGER},
    "procurement.manage": {RestaurantRole.ADMIN, RestaurantRole.BRANCH_MANAGER, RestaurantRole.PURCHASE_MANAGER},
    "billing.settle": {RestaurantRole.ADMIN, RestaurantRole.BRANCH_MANAGER, RestaurantRole.CASHIER, RestaurantRole.ACCOUNTANT},
    "billing.refund": {RestaurantRole.ADMIN, RestaurantRole.BRANCH_MANAGER, RestaurantRole.CASHIER, RestaurantRole.ACCOUNTANT},
    "approval.discount": {RestaurantRole.ADMIN, RestaurantRole.BRANCH_MANAGER},
    "workforce.manage": {RestaurantRole.ADMIN, RestaurantRole.BRANCH_MANAGER},
    "reporting.view": {RestaurantRole.ADMIN, RestaurantRole.BRANCH_MANAGER, RestaurantRole.ACCOUNTANT},
}

_PATH_ACTIONS: list[tuple[str, str]] = [
    ("/api/v1/branches/bootstrap", "branch.bootstrap"),
    ("/api/v1/branches", "branch.configure"),
    ("/api/v1/reservations", "reservation.manage"),
    ("/api/v1/waitlist", "waitlist.manage"),
    ("/api/v1/tables", "tables.manage"),
    ("/api/v1/orders", "orders.manage"),
    ("/api/v1/kitchen", "kitchen.manage"),
    ("/api/v1/inventory", "inventory.manage"),
    ("/api/v1/purchase-orders", "procurement.manage"),
    ("/api/v1/goods-receipts", "procurement.manage"),
    ("/api/v1/bills", "billing.settle"),
    ("/api/v1/refunds", "billing.refund"),
    ("/api/v1/discount-approvals", "approval.discount"),
    ("/api/v1/shifts", "workforce.manage"),
    ("/api/v1/attendance", "workforce.manage"),
    ("/api/v1/reports", "reporting.view"),
    ("/api/v1/accounting-exports", "reporting.view"),
]

PRIVILEGED_ACTIONS: set[str] = {
    "inventory.adjustment.manual",
    "billing.discount.approved",
    "billing.refund.created",
    "reconciliation.override",
}


def resolve_action(path: str) -> str | None:
    for prefix, action in _PATH_ACTIONS:
        if path.startswith(prefix):
            return action
    return None


def role_can_access_action(*, role: RestaurantRole, action: str | None) -> bool:
    if action is None:
        return True
    allowed = _ACTION_PERMISSIONS.get(action)
    if not allowed:
        return True
    return role in allowed
