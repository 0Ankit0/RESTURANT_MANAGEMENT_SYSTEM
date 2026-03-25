import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.apps.core import security
from src.apps.iam.models.user import User
from src.apps.iam.utils.hashid import encode_id
from src.apps.observability.models import ObservabilityLogEntry, SecurityIncident


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


@pytest.mark.integration
class TestObservabilityAPI:
    @pytest.mark.asyncio
    async def test_superuser_can_list_logs_and_summary(self, client: AsyncClient, db_session: AsyncSession):
        admin = await _make_user(
            db_session,
            username="obsadmin",
            email="obsadmin@example.com",
            is_superuser=True,
        )
        token = await _login(client, admin.username)

        logs_response = await client.get(
            "/api/v1/observability/logs",
            headers={"Authorization": f"Bearer {token}"},
        )
        summary_response = await client.get(
            "/api/v1/observability/logs/summary",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert logs_response.status_code == 200, logs_response.text
        assert summary_response.status_code == 200, summary_response.text
        assert "items" in logs_response.json()
        assert "open_incidents" in summary_response.json()

    @pytest.mark.asyncio
    async def test_non_superuser_cannot_access_observability_endpoints(self, client: AsyncClient, db_session: AsyncSession):
        user = await _make_user(
            db_session,
            username="regularobs",
            email="regularobs@example.com",
            is_superuser=False,
        )
        token = await _login(client, user.username)

        response = await client.get(
            "/api/v1/observability/logs",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_failed_login_burst_creates_security_incident(self, client: AsyncClient, db_session: AsyncSession):
        await _make_user(
            db_session,
            username="burstuser",
            email="burstuser@example.com",
        )
        admin = await _make_user(
            db_session,
            username="burstadmin",
            email="burstadmin@example.com",
            is_superuser=True,
        )

        for _ in range(5):
            response = await client.post(
                "/api/v1/auth/login/?set_cookie=false",
                json={"username": "burstuser", "password": "WrongPass123"},
            )
            assert response.status_code == 400

        admin_token = await _login(client, admin.username)
        incidents_response = await client.get(
            "/api/v1/observability/incidents",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"signal_type": "auth.failed_login_burst"},
        )

        assert incidents_response.status_code == 200, incidents_response.text
        items = incidents_response.json()["items"]
        assert items
        assert any(item["signal_type"] == "auth.failed_login_burst" for item in items)

    @pytest.mark.asyncio
    async def test_admin_privilege_change_creates_log_and_incident(self, client: AsyncClient, db_session: AsyncSession):
        admin = await _make_user(
            db_session,
            username="signaladmin",
            email="signaladmin@example.com",
            is_superuser=True,
        )
        target = await _make_user(
            db_session,
            username="targetuser",
            email="targetuser@example.com",
        )
        token = await _login(client, admin.username)

        response = await client.patch(
            f"/api/v1/users/{encode_id(target.id)}",
            headers={"Authorization": f"Bearer {token}"},
            json={"is_superuser": True},
        )
        assert response.status_code == 200, response.text

        incidents = (
            await db_session.execute(
                select(SecurityIncident).where(SecurityIncident.signal_type == "admin.privilege_change")
            )
        ).scalars().all()
        logs = (
            await db_session.execute(
                select(ObservabilityLogEntry).where(ObservabilityLogEntry.event_code == "admin.privilege_change")
            )
        ).scalars().all()

        assert incidents
        assert logs

    @pytest.mark.asyncio
    async def test_admin_can_acknowledge_incident(self, client: AsyncClient, db_session: AsyncSession):
        admin = await _make_user(
            db_session,
            username="reviewadmin",
            email="reviewadmin@example.com",
            is_superuser=True,
        )
        incident = SecurityIncident(
            signal_type="ops.error_spike",
            severity="high",
            status="open",
            title="Server errors",
            summary="Repeated failures",
            fingerprint="ops.error_spike:/health",
        )
        db_session.add(incident)
        await db_session.commit()
        await db_session.refresh(incident)
        token = await _login(client, admin.username)

        response = await client.patch(
            f"/api/v1/observability/incidents/{encode_id(incident.id)}",
            headers={"Authorization": f"Bearer {token}"},
            json={"status": "acknowledged", "review_notes": "Investigating"},
        )

        assert response.status_code == 200, response.text
        assert response.json()["status"] == "acknowledged"
        assert response.json()["review_notes"] == "Investigating"

    @pytest.mark.asyncio
    async def test_rbac_endpoints_require_superuser(self, client: AsyncClient, db_session: AsyncSession):
        user = await _make_user(
            db_session,
            username="rbacviewer",
            email="rbacviewer@example.com",
            is_superuser=False,
        )
        token = await _login(client, user.username)

        response = await client.get(
            "/api/v1/roles",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 403
