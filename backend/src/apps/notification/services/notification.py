"""Notification service — persistence plus multi-channel delivery."""
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from src.apps.notification.models.notification import Notification
from src.apps.notification.models.notification_device import (
    NotificationDevice,
    NotificationDeviceProvider,
)
from src.apps.notification.models.notification_preference import NotificationPreference
from src.apps.notification.schemas.notification import NotificationCreate, NotificationList, NotificationRead
from src.apps.notification.schemas.notification_device import NotificationDeviceCreate
from src.apps.notification.schemas.notification_preference import NotificationPreferenceRead
from src.apps.notification.tasks import (
    send_notification_email_task,
    send_push_notification_task,
    send_sms_notification_task,
)

log = logging.getLogger(__name__)


async def get_or_create_preference(db: AsyncSession, user_id: int) -> NotificationPreference:
    result = await db.execute(
        select(NotificationPreference).where(col(NotificationPreference.user_id) == user_id)
    )
    pref = result.scalars().first()
    if pref is None:
        pref = NotificationPreference(user_id=user_id)
        db.add(pref)
        await db.commit()
        await db.refresh(pref)
    return pref


async def list_devices(db: AsyncSession, user_id: int) -> list[NotificationDevice]:
    result = await db.execute(
        select(NotificationDevice)
        .where(
            and_(
                col(NotificationDevice.user_id) == user_id,
                col(NotificationDevice.is_active) == True,  # noqa: E712
            )
        )
        .order_by(col(NotificationDevice.updated_at).desc())
    )
    return list(result.scalars().all())


async def get_preference_read(
    db: AsyncSession,
    user_id: int,
) -> NotificationPreferenceRead:
    pref = await get_or_create_preference(db, user_id)
    return await serialize_preference(db, pref)


async def serialize_preference(
    db: AsyncSession,
    pref: NotificationPreference,
) -> NotificationPreferenceRead:
    devices = await list_devices(db, pref.user_id)
    push_providers = sorted({device.provider.value for device in devices})
    data = NotificationPreferenceRead.model_validate(pref).model_dump()
    data["push_provider"] = push_providers[0] if len(push_providers) == 1 else None
    data["push_providers"] = push_providers
    return NotificationPreferenceRead.model_validate(data)


async def register_device(
    db: AsyncSession,
    user_id: int,
    payload: NotificationDeviceCreate,
) -> NotificationDevice:
    existing_query = select(NotificationDevice).where(
        NotificationDevice.user_id == user_id,
        NotificationDevice.provider == payload.provider,
    )
    if payload.provider == NotificationDeviceProvider.WEBPUSH:
        existing_query = existing_query.where(NotificationDevice.endpoint == payload.endpoint)
    elif payload.provider == NotificationDeviceProvider.FCM:
        existing_query = existing_query.where(NotificationDevice.token == payload.token)
    else:
        existing_query = existing_query.where(
            NotificationDevice.subscription_id == payload.subscription_id
        )
    result = await db.execute(existing_query)
    device = result.scalars().first()
    if device is None:
        device = NotificationDevice(user_id=user_id, provider=payload.provider, platform=payload.platform)
    device.token = payload.token
    device.endpoint = payload.endpoint
    device.p256dh = payload.p256dh
    device.auth = payload.auth
    device.subscription_id = payload.subscription_id
    device.device_metadata = payload.device_metadata
    device.is_active = True
    device.last_seen_at = datetime.now()
    device.updated_at = datetime.now()
    db.add(device)
    await db.commit()
    await db.refresh(device)
    await _sync_preference_push_fields(db, user_id)
    return device


async def remove_device(db: AsyncSession, user_id: int, device_id: int) -> bool:
    device = await db.get(NotificationDevice, device_id)
    if not device or device.user_id != user_id:
        return False
    device.is_active = False
    device.updated_at = datetime.now()
    db.add(device)
    await db.commit()
    await _sync_preference_push_fields(db, user_id)
    return True


async def remove_webpush_subscription(db: AsyncSession, user_id: int) -> None:
    result = await db.execute(
        select(NotificationDevice).where(
            NotificationDevice.user_id == user_id,
            NotificationDevice.provider == NotificationDeviceProvider.WEBPUSH,
            NotificationDevice.is_active == True,  # noqa: E712
        )
    )
    for device in result.scalars().all():
        device.is_active = False
        device.updated_at = datetime.now()
        db.add(device)
    await db.commit()
    await _sync_preference_push_fields(db, user_id)


async def _sync_preference_push_fields(db: AsyncSession, user_id: int) -> NotificationPreference:
    pref = await get_or_create_preference(db, user_id)
    devices = await list_devices(db, user_id)
    webpush_device = next(
        (device for device in devices if device.provider == NotificationDeviceProvider.WEBPUSH),
        None,
    )
    pref.push_endpoint = webpush_device.endpoint if webpush_device else None
    pref.push_p256dh = webpush_device.p256dh if webpush_device else None
    pref.push_auth = webpush_device.auth if webpush_device else None
    pref.push_enabled = pref.push_enabled if devices else False
    db.add(pref)
    await db.commit()
    await db.refresh(pref)
    return pref


async def create_notification(
    db: AsyncSession,
    data: NotificationCreate,
    push_ws: bool = True,
) -> Notification:
    notification = Notification(
        user_id=data.user_id,
        title=data.title,
        body=data.body,
        type=data.type,
        extra_data=data.extra_data,
    )
    db.add(notification)
    await db.commit()
    await db.refresh(notification)

    pref = await get_or_create_preference(db, data.user_id)

    if push_ws and pref.websocket_enabled:
        await _push_to_ws(notification)
    if pref.email_enabled:
        await _push_to_email(db, notification)
    if pref.push_enabled:
        await _push_to_devices(db, notification)
    if pref.sms_enabled:
        await _push_to_sms(db, notification)

    return notification


async def _push_to_ws(notification: Notification) -> None:
    try:
        from src.apps.websocket.manager import manager

        await manager.push_event(
            user_id=notification.user_id,
            event="notification.new",
            data={
                "id": notification.id,
                "title": notification.title,
                "body": notification.body,
                "type": notification.type,
                "is_read": notification.is_read,
                "extra_data": notification.extra_data,
                "created_at": notification.created_at.isoformat(),
            },
        )
    except Exception as exc:
        log.warning("WS push failed for notification id=%s: %s", notification.id, exc)


async def _push_to_email(db: AsyncSession, notification: Notification) -> None:
    try:
        from src.apps.iam.models.user import User

        result = await db.execute(select(User).where(col(User.id) == notification.user_id))
        user = result.scalars().first()
        if not user:
            return
        send_notification_email_task.delay(
            recipients=[{"name": user.username, "email": user.email}],
            subject=notification.title,
            context={
                "user": {"email": user.email, "first_name": user.username},
                "notification": {
                    "title": notification.title,
                    "body": notification.body,
                    "type": notification.type,
                },
            },
        )
    except Exception as exc:
        log.warning("Email push failed for notification id=%s: %s", notification.id, exc)


async def _push_to_devices(db: AsyncSession, notification: Notification) -> None:
    devices = await list_devices(db, notification.user_id)
    for device in devices:
        try:
            payload = {
                "provider": device.provider.value,
                "platform": device.platform.value,
                "title": notification.title,
                "body": notification.body,
                "data": notification.extra_data if isinstance(notification.extra_data, dict) else None,
                "token": device.token,
                "endpoint": device.endpoint,
                "p256dh": device.p256dh,
                "auth": device.auth,
                "subscription_id": device.subscription_id,
            }
            send_push_notification_task.delay(payload)
        except Exception as exc:
            log.warning(
                "Push task enqueue failed for notification id=%s device=%s: %s",
                notification.id,
                device.id,
                exc,
            )


async def _push_to_sms(db: AsyncSession, notification: Notification) -> None:
    try:
        from src.apps.iam.models.user import UserProfile

        result = await db.execute(
            select(UserProfile).where(col(UserProfile.user_id) == notification.user_id)
        )
        profile = result.scalars().first()
        if not profile or not profile.phone:
            return
        send_sms_notification_task.delay(
            to_number=profile.phone,
            body=f"{notification.title}: {notification.body}",
        )
    except Exception as exc:
        log.warning("SMS task enqueue failed for notification id=%s: %s", notification.id, exc)


async def get_user_notifications(
    db: AsyncSession,
    user_id: int,
    *,
    unread_only: bool = False,
    skip: int = 0,
    limit: int = 20,
) -> NotificationList:
    base_query = select(Notification).where(col(Notification.user_id) == user_id)
    if unread_only:
        base_query = base_query.where(col(Notification.is_read) == False)  # noqa: E712

    count_result = await db.execute(select(func.count()).select_from(base_query.subquery()))
    total = count_result.scalar_one()
    unread_result = await db.execute(
        select(func.count()).select_from(
            select(Notification)
            .where(and_(col(Notification.user_id) == user_id, col(Notification.is_read) == False))  # noqa: E712
            .subquery()
        )
    )
    unread_count = unread_result.scalar_one()
    result = await db.execute(
        base_query.order_by(col(Notification.created_at).desc()).offset(skip).limit(limit)
    )
    items = result.scalars().all()
    return NotificationList(
        items=[NotificationRead.model_validate(item) for item in items],
        total=total,
        unread_count=unread_count,
    )


async def get_notification(db: AsyncSession, notification_id: int, user_id: int) -> Optional[Notification]:
    result = await db.execute(
        select(Notification).where(
            and_(
                col(Notification.id) == notification_id,
                col(Notification.user_id) == user_id,
            )
        )
    )
    return result.scalars().first()


async def mark_as_read(
    db: AsyncSession,
    notification_id: int,
    user_id: int,
) -> Optional[Notification]:
    notification = await get_notification(db, notification_id, user_id)
    if not notification:
        return None
    notification.is_read = True
    db.add(notification)
    await db.commit()
    await db.refresh(notification)
    return notification


async def mark_all_read(db: AsyncSession, user_id: int) -> int:
    result = await db.execute(
        select(Notification).where(
            and_(col(Notification.user_id) == user_id, col(Notification.is_read) == False)  # noqa: E712
        )
    )
    notifications = result.scalars().all()
    for notification in notifications:
        notification.is_read = True
        db.add(notification)
    await db.commit()
    return len(notifications)


async def delete_notification(db: AsyncSession, notification_id: int, user_id: int) -> bool:
    notification = await get_notification(db, notification_id, user_id)
    if not notification:
        return False
    await db.delete(notification)
    await db.commit()
    return True
