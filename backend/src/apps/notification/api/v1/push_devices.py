"""Push-device registration and public push-config API."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.communications import get_communications_service
from src.apps.core.config import settings
from src.apps.iam.api.deps import get_current_user, get_db
from src.apps.iam.models.user import User
from src.apps.iam.utils.hashid import decode_id_or_404
from src.apps.notification.models.notification_device import NotificationDevicePlatform, NotificationDeviceProvider
from src.apps.notification.schemas.notification_device import (
    FcmDeviceCreate,
    NotificationDeviceCreate,
    NotificationDeviceRead,
    OneSignalDeviceCreate,
    WebPushDeviceCreate,
)
from src.apps.notification.schemas.notification_preference import (
    NotificationPreferenceRead,
    PushSubscriptionUpdate,
)
from src.apps.notification.services.notification import (
    get_or_create_preference,
    list_devices,
    register_device,
    remove_device,
    remove_webpush_subscription,
    serialize_preference,
)

router = APIRouter()


def _require_push_enabled() -> None:
    if not settings.PUSH_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Push notifications are currently disabled.",
        )


def _require_push_provider(provider: NotificationDeviceProvider) -> None:
    _require_push_enabled()
    comms = get_communications_service()
    if not comms.is_push_provider_available(provider.value):
        available = comms.get_available_push_providers()
        available_detail = ", ".join(available) if available else "none"
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                f"Push provider '{provider.value}' is not configured. "
                f"Available push providers: {available_detail}."
            ),
        )


async def _register_and_enable_push(
    payload: NotificationDeviceCreate,
    current_user: User,
    db: AsyncSession,
) -> NotificationDeviceRead:
    assert isinstance(current_user.id, int), "User Id can't be None"
    _require_push_provider(payload.provider)
    device = await register_device(db, current_user.id, payload)
    pref = await get_or_create_preference(db, current_user.id)
    pref.push_enabled = True
    db.add(pref)
    await db.commit()
    await db.refresh(device)
    return NotificationDeviceRead.model_validate(device)


@router.get("/devices/", response_model=list[NotificationDeviceRead])
async def get_notification_devices(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[NotificationDeviceRead]:
    _require_push_enabled()
    assert isinstance(current_user.id, int), "User Id can't be None"
    devices = await list_devices(db, current_user.id)
    return [NotificationDeviceRead.model_validate(device) for device in devices]


@router.post("/devices/", response_model=NotificationDeviceRead, status_code=status.HTTP_201_CREATED)
async def create_notification_device(
    data: NotificationDeviceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NotificationDeviceRead:
    return await _register_and_enable_push(data, current_user, db)


@router.post(
    "/devices/webpush/",
    response_model=NotificationDeviceRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_webpush_device(
    data: WebPushDeviceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NotificationDeviceRead:
    return await _register_and_enable_push(data.to_device_create(), current_user, db)


@router.post(
    "/devices/fcm/",
    response_model=NotificationDeviceRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_fcm_device(
    data: FcmDeviceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NotificationDeviceRead:
    return await _register_and_enable_push(data.to_device_create(), current_user, db)


@router.post(
    "/devices/onesignal/",
    response_model=NotificationDeviceRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_onesignal_device(
    data: OneSignalDeviceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NotificationDeviceRead:
    return await _register_and_enable_push(data.to_device_create(), current_user, db)


@router.delete("/devices/{device_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification_device(
    device_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    _require_push_enabled()
    assert isinstance(current_user.id, int), "User Id can't be None"
    removed = await remove_device(db, current_user.id, decode_id_or_404(device_id))
    if not removed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")


@router.get("/push/config/")
async def get_push_config() -> dict:
    _require_push_enabled()
    return get_communications_service().get_push_public_config()


@router.put("/preferences/push-subscription/", response_model=NotificationPreferenceRead)
async def register_push_subscription(
    data: PushSubscriptionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NotificationPreferenceRead:
    _require_push_provider(NotificationDeviceProvider.WEBPUSH)
    assert isinstance(current_user.id, int), "User Id can't be None"
    await register_device(
        db,
        current_user.id,
        NotificationDeviceCreate(
            provider=NotificationDeviceProvider.WEBPUSH,
            platform=NotificationDevicePlatform.WEB,
            endpoint=data.endpoint,
            p256dh=data.p256dh,
            auth=data.auth,
        ),
    )
    pref = await get_or_create_preference(db, current_user.id)
    pref.push_enabled = True
    db.add(pref)
    await db.commit()
    await db.refresh(pref)
    return await serialize_preference(db, pref)


@router.delete("/preferences/push-subscription/", status_code=status.HTTP_204_NO_CONTENT)
async def remove_push_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    _require_push_enabled()
    assert isinstance(current_user.id, int), "User Id can't be None"
    await remove_webpush_subscription(db, current_user.id)
