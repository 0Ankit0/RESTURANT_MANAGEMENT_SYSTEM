"""Unit tests for the notification module (service + REST API)."""
import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.core import security
from src.apps.core.config import settings
from src.apps.notification.models.notification import Notification, NotificationType
from src.apps.notification.schemas.notification import NotificationCreate
from src.apps.notification.services.notification import (
    create_notification,
    delete_notification,
    get_notification,
    get_user_notifications,
    mark_all_read,
    mark_as_read,
)
from tests.factories import UserFactory


# ── helpers ──────────────────────────────────────────────────────────────────

async def _make_user(db: AsyncSession, **kwargs):
    defaults = dict(
        username="notifuser",
        email="notif@example.com",
        hashed_password=security.get_password_hash("TestPass123"),
        is_active=True,
        is_confirmed=True,
    )
    defaults.update(kwargs)
    user = UserFactory.build(**defaults)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def _login(client: AsyncClient, username: str, password: str = "TestPass123") -> str:
    resp = await client.post(
        "/api/v1/auth/login/?set_cookie=false",
        json={"username": username, "password": password},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access"]


# ── service tests ─────────────────────────────────────────────────────────────


@pytest.mark.unit
class TestNotificationService:

    @pytest.mark.asyncio
    async def test_create_notification_persisted(self, db_session: AsyncSession):
        user = await _make_user(db_session)
        data = NotificationCreate(
            user_id=user.id, title="Hello", body="World", type=NotificationType.INFO
        )
        with patch(
            "src.apps.notification.services.notification._push_to_ws",
            new_callable=AsyncMock,
        ) as mock_push:
            notification = await create_notification(db_session, data, push_ws=True)

        assert notification.id is not None
        assert notification.title == "Hello"
        assert notification.is_read is False
        mock_push.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_notification_no_ws(self, db_session: AsyncSession):
        user = await _make_user(db_session, username="notifuser2", email="notif2@example.com")
        data = NotificationCreate(user_id=user.id, title="T", body="B")
        notification = await create_notification(db_session, data, push_ws=False)
        assert notification.id is not None

    @pytest.mark.asyncio
    async def test_get_user_notifications(self, db_session: AsyncSession):
        user = await _make_user(db_session, username="notifuser3", email="notif3@example.com")
        for i in range(3):
            db_session.add(Notification(user_id=user.id, title=f"N{i}", body="body"))
        await db_session.commit()

        result = await get_user_notifications(db_session, user.id, limit=10)
        assert result.total == 3
        assert result.unread_count == 3
        assert len(result.items) == 3

    @pytest.mark.asyncio
    async def test_mark_as_read(self, db_session: AsyncSession):
        user = await _make_user(db_session, username="notifuser4", email="notif4@example.com")
        n = Notification(user_id=user.id, title="T", body="B")
        db_session.add(n)
        await db_session.commit()
        await db_session.refresh(n)

        updated = await mark_as_read(db_session, n.id, user.id)
        assert updated is not None
        assert updated.is_read is True

    @pytest.mark.asyncio
    async def test_mark_all_read(self, db_session: AsyncSession):
        user = await _make_user(db_session, username="notifuser5", email="notif5@example.com")
        for _ in range(4):
            db_session.add(Notification(user_id=user.id, title="T", body="B"))
        await db_session.commit()

        count = await mark_all_read(db_session, user.id)
        assert count == 4

        result = await get_user_notifications(db_session, user.id, unread_only=True)
        assert result.total == 0

    @pytest.mark.asyncio
    async def test_delete_notification(self, db_session: AsyncSession):
        user = await _make_user(db_session, username="notifuser6", email="notif6@example.com")
        n = Notification(user_id=user.id, title="T", body="B")
        db_session.add(n)
        await db_session.commit()
        await db_session.refresh(n)

        deleted = await delete_notification(db_session, n.id, user.id)
        assert deleted is True

        gone = await get_notification(db_session, n.id, user.id)
        assert gone is None

    @pytest.mark.asyncio
    async def test_delete_notification_not_found(self, db_session: AsyncSession):
        user = await _make_user(db_session, username="notifuser7", email="notif7@example.com")
        deleted = await delete_notification(db_session, 99999, user.id)
        assert deleted is False


# ── REST API tests ────────────────────────────────────────────────────────────


@pytest.mark.unit
class TestNotificationAPI:

    @pytest.fixture(autouse=True)
    def restore_push_settings(self):
        original = {
            "PUSH_ENABLED": settings.PUSH_ENABLED,
            "VAPID_PUBLIC_KEY": settings.VAPID_PUBLIC_KEY,
            "VAPID_PRIVATE_KEY": settings.VAPID_PRIVATE_KEY,
            "FCM_SERVER_KEY": settings.FCM_SERVER_KEY,
            "FCM_PROJECT_ID": settings.FCM_PROJECT_ID,
            "FCM_SERVICE_ACCOUNT_JSON": settings.FCM_SERVICE_ACCOUNT_JSON,
            "FCM_SERVICE_ACCOUNT_FILE": settings.FCM_SERVICE_ACCOUNT_FILE,
            "ONESIGNAL_APP_ID": settings.ONESIGNAL_APP_ID,
            "ONESIGNAL_API_KEY": settings.ONESIGNAL_API_KEY,
        }
        yield
        for key, value in original.items():
            setattr(settings, key, value)

    def _enable_webpush(self) -> None:
        settings.PUSH_ENABLED = True
        settings.VAPID_PUBLIC_KEY = "test-vapid-public"
        settings.VAPID_PRIVATE_KEY = "test-vapid-private"

    def _enable_fcm(self) -> None:
        settings.PUSH_ENABLED = True
        settings.FCM_SERVER_KEY = "test-fcm-server-key"

    def _enable_onesignal(self) -> None:
        settings.PUSH_ENABLED = True
        settings.ONESIGNAL_APP_ID = "test-onesignal-app-id"
        settings.ONESIGNAL_API_KEY = "test-onesignal-api-key"

    @pytest.mark.asyncio
    async def test_list_notifications_empty(self, client: AsyncClient, db_session: AsyncSession):
        await _make_user(db_session, username="apiuser1", email="api1@example.com")
        token = await _login(client, "apiuser1")
        resp = await client.get(
            "/api/v1/notifications/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["unread_count"] == 0

    @pytest.mark.asyncio
    async def test_list_notifications_with_data(self, client: AsyncClient, db_session: AsyncSession):
        user = await _make_user(db_session, username="apiuser2", email="api2@example.com")
        db_session.add(Notification(user_id=user.id, title="A", body="B"))
        db_session.add(Notification(user_id=user.id, title="C", body="D"))
        await db_session.commit()

        token = await _login(client, "apiuser2")
        resp = await client.get(
            "/api/v1/notifications/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 2

    @pytest.mark.asyncio
    async def test_mark_single_read(self, client: AsyncClient, db_session: AsyncSession):
        user = await _make_user(db_session, username="apiuser3", email="api3@example.com")
        n = Notification(user_id=user.id, title="T", body="B")
        db_session.add(n)
        await db_session.commit()
        await db_session.refresh(n)

        token = await _login(client, "apiuser3")
        resp = await client.patch(
            f"/api/v1/notifications/{n.id}/read/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["is_read"] is True

    @pytest.mark.asyncio
    async def test_mark_all_read_endpoint(self, client: AsyncClient, db_session: AsyncSession):
        user = await _make_user(db_session, username="apiuser4", email="api4@example.com")
        for _ in range(3):
            db_session.add(Notification(user_id=user.id, title="X", body="Y"))
        await db_session.commit()

        token = await _login(client, "apiuser4")
        resp = await client.patch(
            "/api/v1/notifications/read-all/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["updated"] == 3

    @pytest.mark.asyncio
    async def test_delete_notification_endpoint(self, client: AsyncClient, db_session: AsyncSession):
        user = await _make_user(db_session, username="apiuser5", email="api5@example.com")
        n = Notification(user_id=user.id, title="Del", body="Me")
        db_session.add(n)
        await db_session.commit()
        await db_session.refresh(n)

        token = await _login(client, "apiuser5")
        resp = await client.delete(
            f"/api/v1/notifications/{n.id}/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_notification_not_found(self, client: AsyncClient, db_session: AsyncSession):
        await _make_user(db_session, username="apiuser6", email="api6@example.com")
        token = await _login(client, "apiuser6")
        resp = await client.delete(
            "/api/v1/notifications/99999/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_create_notification_requires_superuser(self, client: AsyncClient, db_session: AsyncSession):
        user = await _make_user(db_session, username="apiuser7", email="api7@example.com")
        token = await _login(client, "apiuser7")
        resp = await client.post(
            "/api/v1/notifications/",
            json={"user_id": user.id, "title": "T", "body": "B", "type": "info"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_create_notification_as_superuser(self, client: AsyncClient, db_session: AsyncSession):
        target = await _make_user(db_session, username="target1", email="target1@example.com")
        await _make_user(db_session, username="suadmin", email="suadmin@example.com", is_superuser=True)
        token = await _login(client, "suadmin")

        with patch(
            "src.apps.notification.services.notification._push_to_ws",
            new_callable=AsyncMock,
        ):
            resp = await client.post(
                "/api/v1/notifications/",
                json={"user_id": target.id, "title": "Hi", "body": "There", "type": "success"},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Hi"
        assert data["type"] == "success"

    @pytest.mark.asyncio
    async def test_register_and_list_notification_devices(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        self._enable_webpush()
        await _make_user(db_session, username="apiuser8", email="api8@example.com")
        token = await _login(client, "apiuser8")

        create_resp = await client.post(
            "/api/v1/notifications/devices/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "provider": "webpush",
                "platform": "web",
                "endpoint": "https://push.example.com/subscription",
                "p256dh": "test-p256dh",
                "auth": "test-auth",
            },
        )
        assert create_resp.status_code == 201, create_resp.text
        assert create_resp.json()["provider"] == "webpush"

        list_resp = await client.get(
            "/api/v1/notifications/devices/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert list_resp.status_code == 200
        devices = list_resp.json()
        assert len(devices) == 1
        assert devices[0]["platform"] == "web"

    @pytest.mark.asyncio
    async def test_push_subscription_compatibility_wrapper_uses_device_registry(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        self._enable_webpush()
        await _make_user(db_session, username="apiuser9", email="api9@example.com")
        token = await _login(client, "apiuser9")

        put_resp = await client.put(
            "/api/v1/notifications/preferences/push-subscription/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "endpoint": "https://push.example.com/subscription-2",
                "p256dh": "compat-p256dh",
                "auth": "compat-auth",
            },
        )
        assert put_resp.status_code == 200, put_resp.text
        assert put_resp.json()["push_enabled"] is True

        devices_resp = await client.get(
            "/api/v1/notifications/devices/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert devices_resp.status_code == 200
        assert len(devices_resp.json()) == 1

        delete_resp = await client.delete(
            "/api/v1/notifications/preferences/push-subscription/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert delete_resp.status_code == 204

        devices_after = await client.get(
            "/api/v1/notifications/devices/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert devices_after.status_code == 200
        assert devices_after.json() == []

    @pytest.mark.asyncio
    async def test_register_fcm_device_with_provider_specific_endpoint(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        self._enable_fcm()
        await _make_user(db_session, username="apiuser10", email="api10@example.com")
        token = await _login(client, "apiuser10")

        resp = await client.post(
            "/api/v1/notifications/devices/fcm/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "platform": "android",
                "token": "fcm-device-token",
                "device_metadata": {"app_version": "1.0.0"},
            },
        )

        assert resp.status_code == 201, resp.text
        assert resp.json()["provider"] == "fcm"
        assert resp.json()["token"] == "fcm-device-token"

    @pytest.mark.asyncio
    async def test_register_onesignal_device_with_provider_specific_endpoint(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        self._enable_onesignal()
        await _make_user(db_session, username="apiuser11", email="api11@example.com")
        token = await _login(client, "apiuser11")

        resp = await client.post(
            "/api/v1/notifications/devices/onesignal/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "platform": "ios",
                "subscription_id": "onesignal-subscription-id",
            },
        )

        assert resp.status_code == 201, resp.text
        assert resp.json()["provider"] == "onesignal"
        assert resp.json()["subscription_id"] == "onesignal-subscription-id"

    @pytest.mark.asyncio
    async def test_push_endpoints_return_503_when_push_disabled(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        settings.PUSH_ENABLED = False
        await _make_user(db_session, username="apiuser12", email="api12@example.com")
        token = await _login(client, "apiuser12")

        resp = await client.get(
            "/api/v1/notifications/push/config/",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert resp.status_code == 503
        assert "disabled" in resp.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_register_device_rejects_unconfigured_provider(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        self._enable_webpush()
        settings.FCM_SERVER_KEY = ""
        settings.FCM_PROJECT_ID = ""
        settings.FCM_SERVICE_ACCOUNT_JSON = ""
        settings.FCM_SERVICE_ACCOUNT_FILE = ""
        await _make_user(db_session, username="apiuser13", email="api13@example.com")
        token = await _login(client, "apiuser13")

        resp = await client.post(
            "/api/v1/notifications/devices/fcm/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "platform": "android",
                "token": "fcm-device-token",
            },
        )

        assert resp.status_code == 503
        assert "not configured" in resp.json()["detail"].lower()
