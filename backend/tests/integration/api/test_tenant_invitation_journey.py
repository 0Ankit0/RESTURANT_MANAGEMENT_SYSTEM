from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.apps.iam.casbin_enforcer import CasbinEnforcer
from src.apps.multitenancy.models.tenant import TenantInvitation


async def _signup_and_get_token(client: AsyncClient, username: str, email: str) -> str:
    response = await client.post(
        "/api/v1/auth/signup/?set_cookie=false",
        json={
            "username": username,
            "email": email,
            "password": "Passw0rd!123",
            "confirm_password": "Passw0rd!123",
            "first_name": username,
            "last_name": "User",
        },
    )
    assert response.status_code == 200
    return response.json()["access"]


@pytest.mark.asyncio
async def test_tenant_invitation_accept_role_change_journey(
    client: AsyncClient,
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
):
    add_role_mock = AsyncMock(return_value=True)
    remove_role_mock = AsyncMock(return_value=True)
    monkeypatch.setattr(CasbinEnforcer, "add_role_for_user", add_role_mock)
    monkeypatch.setattr(CasbinEnforcer, "remove_role_for_user", remove_role_mock)

    owner_token = await _signup_and_get_token(client, "tenant_owner", "owner@tenant.test")
    member_token = await _signup_and_get_token(client, "tenant_member", "member@tenant.test")

    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    member_headers = {"Authorization": f"Bearer {member_token}"}

    create_tenant_response = await client.post(
        "/api/v1/tenants/",
        json={"name": "Journey Tenant", "slug": "journey-tenant", "description": "integration"},
        headers=owner_headers,
    )
    assert create_tenant_response.status_code == 201
    tenant = create_tenant_response.json()
    tenant_id = tenant["id"]

    invite_response = await client.post(
        f"/api/v1/tenants/{tenant_id}/invitations",
        json={"email": "member@tenant.test", "role": "member"},
        headers=owner_headers,
    )
    assert invite_response.status_code == 201
    invitation_row = (
        await db_session.execute(
            select(TenantInvitation).where(
                TenantInvitation.tenant_id.is_not(None),
                TenantInvitation.email == "member@tenant.test",
            )
        )
    ).scalars().first()
    assert invitation_row is not None

    accept_response = await client.post(
        "/api/v1/tenants/invitations/accept",
        json={"token": invitation_row.token},
        headers=member_headers,
    )
    assert accept_response.status_code == 200
    accepted_member = accept_response.json()
    assert accepted_member["role"] == "member"

    promote_response = await client.patch(
        f"/api/v1/tenants/{tenant_id}/members/{accepted_member['user_id']}",
        json={"role": "admin"},
        headers=owner_headers,
    )
    assert promote_response.status_code == 200
    assert promote_response.json()["role"] == "admin"

    members_response = await client.get(f"/api/v1/tenants/{tenant_id}/members", headers=owner_headers)
    assert members_response.status_code == 200
    roles_by_user = {item["user_id"]: item["role"] for item in members_response.json()["items"]}
    assert roles_by_user[accepted_member["user_id"]] == "admin"

    assert add_role_mock.await_count >= 3
    add_calls = [tuple(call.args[:3]) for call in add_role_mock.await_args_list]
    assert any(role == "member" and domain == "journey-tenant" for _, role, domain in add_calls)
    assert any(role == "admin" and domain == "journey-tenant" for _, role, domain in add_calls)
    remove_calls = [tuple(call.args[:3]) for call in remove_role_mock.await_args_list]
    assert any(role == "member" and domain == "journey-tenant" for _, role, domain in remove_calls)
