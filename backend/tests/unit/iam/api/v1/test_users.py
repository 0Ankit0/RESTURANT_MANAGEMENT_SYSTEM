import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.apps.core import security
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


@pytest.mark.unit
class TestUserManagementAPI:
    @pytest.mark.asyncio
    async def test_admin_can_update_user_status_and_role(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        admin = await _make_user(
            db_session,
            username="adminusers",
            email="adminusers@example.com",
            is_superuser=True,
        )
        target = await _make_user(
            db_session,
            username="manageduser",
            email="managed@example.com",
            is_active=True,
            is_superuser=False,
        )
        token = await _login(client, admin.username)

        response = await client.patch(
            f"/api/v1/users/{encode_id(target.id)}",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "email": "managed-updated@example.com",
                "first_name": "Managed",
                "last_name": "User",
                "phone": "9800000000",
                "is_active": False,
                "is_superuser": True,
            },
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["email"] == "managed-updated@example.com"
        assert data["first_name"] == "Managed"
        assert data["is_active"] is False
        assert data["is_superuser"] is True

        refreshed = await db_session.execute(select(User).where(User.id == target.id))
        user = refreshed.scalars().one()
        assert user.email == "managed-updated@example.com"
        assert user.is_active is False
        assert user.is_superuser is True
        assert user.profile is not None
        assert user.profile.first_name == "Managed"
        assert user.profile.phone == "9800000000"

    @pytest.mark.asyncio
    async def test_admin_list_users_endpoint_returns_paginated_users(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        admin = await _make_user(
            db_session,
            username="listadmin",
            email="listadmin@example.com",
            is_superuser=True,
        )
        await _make_user(db_session, username="firstuser", email="first@example.com")
        await _make_user(db_session, username="seconduser", email="second@example.com")
        token = await _login(client, admin.username)

        response = await client.get(
            "/api/v1/users/?skip=0&limit=10&search=user",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["total"] >= 2
        assert len(data["items"]) >= 2
