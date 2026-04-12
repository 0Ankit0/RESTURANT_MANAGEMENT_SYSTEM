from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.core import security
from src.apps.iam.casbin_enforcer import CasbinEnforcer
from src.apps.iam.models.user import User
from src.apps.iam.utils.hashid import encode_id


async def _make_user(db: AsyncSession, **kwargs) -> User:
    user = User(
        username=kwargs.get("username", "user"),
        email=kwargs.get("email", "user@example.com"),
        hashed_password=security.get_password_hash(kwargs.get("password", "TestPass123")),
        is_active=kwargs.get("is_active", True),
        is_superuser=kwargs.get("is_superuser", False),
        is_confirmed=kwargs.get("is_confirmed", True),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def _login(client: AsyncClient, username: str, password: str = "TestPass123") -> str:
    response = await client.post(
        "/api/v1/auth/login/?set_cookie=false",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()["access"]


@pytest.mark.asyncio
async def test_rbac_bootstrap_is_idempotent(client: AsyncClient, db_session: AsyncSession):
    admin = await _make_user(
        db_session,
        username="rbacbootstrapadmin",
        email="rbacbootstrapadmin@example.com",
        is_superuser=True,
    )
    token = await _login(client, admin.username)
    headers = {"Authorization": f"Bearer {token}"}

    first = await client.post("/api/v1/bootstrap", headers=headers, json={"version": "2026.04.12"})
    second = await client.post("/api/v1/bootstrap", headers=headers, json={"version": "2026.04.12"})

    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert first.json()["applied"] is True
    assert second.json()["applied"] is False
    assert second.json()["run_count"] == first.json()["run_count"] + 1


@pytest.mark.asyncio
async def test_tenant_role_transition_propagates_to_casbin(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
):
    add_role_mock = AsyncMock(return_value=True)
    remove_role_mock = AsyncMock(return_value=True)
    monkeypatch.setattr(CasbinEnforcer, "add_role_for_user", add_role_mock)
    monkeypatch.setattr(CasbinEnforcer, "remove_role_for_user", remove_role_mock)

    owner_token = (await client.post(
        "/api/v1/auth/signup/?set_cookie=false",
        json={
            "username": "tenant_owner2",
            "email": "owner2@tenant.test",
            "password": "Passw0rd!123",
            "confirm_password": "Passw0rd!123",
            "first_name": "Owner",
            "last_name": "User",
        },
    )).json()["access"]
    member_token = (await client.post(
        "/api/v1/auth/signup/?set_cookie=false",
        json={
            "username": "tenant_member2",
            "email": "member2@tenant.test",
            "password": "Passw0rd!123",
            "confirm_password": "Passw0rd!123",
            "first_name": "Member",
            "last_name": "User",
        },
    )).json()["access"]
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    member_headers = {"Authorization": f"Bearer {member_token}"}

    tenant = (await client.post(
        "/api/v1/tenants/",
        json={"name": "Journey Tenant 2", "slug": "journey-tenant-2", "description": "integration"},
        headers=owner_headers,
    )).json()
    invitation = await client.post(
        f"/api/v1/tenants/{tenant['id']}/invitations",
        json={"email": "member2@tenant.test", "role": "member"},
        headers=owner_headers,
    )
    assert invitation.status_code == 201
    invitation_id = invitation.json()["id"]

    listed = await client.get(f"/api/v1/tenants/{tenant['id']}/invitations", headers=owner_headers)
    token = listed.json()["items"][0]["token"]
    accepted = await client.post(
        "/api/v1/tenants/invitations/accept",
        json={"token": token},
        headers=member_headers,
    )
    assert accepted.status_code == 200
    member_id = accepted.json()["user_id"]

    promote = await client.patch(
        f"/api/v1/tenants/{tenant['id']}/members/{member_id}",
        json={"role": "admin"},
        headers=owner_headers,
    )
    assert promote.status_code == 200
    demote = await client.patch(
        f"/api/v1/tenants/{tenant['id']}/members/{member_id}",
        json={"role": "member"},
        headers=owner_headers,
    )
    assert demote.status_code == 200
    removed = await client.delete(f"/api/v1/tenants/{tenant['id']}/members/{member_id}", headers=owner_headers)
    assert removed.status_code == 204
    revoke_invitation = await client.delete(
        f"/api/v1/tenants/{tenant['id']}/invitations/{invitation_id}",
        headers=owner_headers,
    )
    assert revoke_invitation.status_code in (204, 400, 404)

    add_calls = [tuple(call.args[:3]) for call in add_role_mock.await_args_list]
    remove_calls = [tuple(call.args[:3]) for call in remove_role_mock.await_args_list]
    assert any(role == "admin" and domain == "journey-tenant-2" for _, role, domain in add_calls)
    assert any(role == "admin" and domain == "journey-tenant-2" for _, role, domain in remove_calls)
    assert any(role == "member" and domain == "journey-tenant-2" for _, role, domain in add_calls)


@pytest.mark.asyncio
async def test_branch_scoped_permission_denial_and_allow(client: AsyncClient, db_session: AsyncSession):
    admin = await _make_user(
        db_session,
        username="rbacscopeadmin",
        email="rbacscopeadmin@example.com",
        is_superuser=True,
    )
    staff = await _make_user(
        db_session,
        username="branchstaff",
        email="branchstaff@example.com",
    )
    token = await _login(client, admin.username)
    headers = {"Authorization": f"Bearer {token}"}

    role = (await client.post("/api/v1/roles", headers=headers, json={"name": "branch_reader", "description": "reader"})).json()
    permission = (
        await client.post(
            "/api/v1/permissions",
            headers=headers,
            json={"resource": "branch.report", "action": "read", "description": "read branch report"},
        )
    ).json()
    await client.post(
        "/api/v1/roles/assign-permission",
        headers=headers,
        json={"role_id": role["id"], "permission_id": permission["id"]},
    )

    denied = await client.get(
        f"/api/v1/effective-permissions/{encode_id(staff.id)}",
        headers=headers,
        params={"branch_id": 99},
    )
    assert denied.status_code == 200
    assert denied.json()["permissions"] == []

    await CasbinEnforcer.add_role_for_user(str(staff.id), "branch_reader", "branch:99")
    await CasbinEnforcer.add_policy("branch_reader", "branch.report", "read", "branch:99")

    allowed = await client.get(
        f"/api/v1/effective-permissions/{encode_id(staff.id)}",
        headers=headers,
        params={"branch_id": 99},
    )
    assert allowed.status_code == 200
    assert any(
        p["resource"] == "branch.report" and p["action"] == "read" and p["domain"] == "branch:99"
        for p in allowed.json()["permissions"]
    )
