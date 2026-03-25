"""
Notification REST API.

Endpoints
─────────
  GET    /notifications/              — list current user's notifications
  POST   /notifications/              — create a notification (superuser only)
  PATCH  /notifications/read-all/     — mark all notifications as read
  PATCH  /notifications/{id}/read/    — mark a single notification as read
  DELETE /notifications/{id}/         — delete a notification
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.iam.api.deps import get_current_active_superuser, get_current_user, get_db
from src.apps.iam.models.user import User
from src.apps.iam.utils.hashid import decode_id_or_404
from src.apps.notification.schemas.notification import (
    NotificationCreate,
    NotificationList,
    NotificationRead,
)
from src.apps.notification.services.notification import (
    create_notification,
    delete_notification,
    get_notification,
    get_user_notifications,
    mark_all_read,
    mark_as_read,
)

router = APIRouter()


@router.get("/", response_model=NotificationList, summary="List notifications")
async def list_notifications(
    unread_only: bool = Query(False, description="Return only unread notifications"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NotificationList:
    """Return paginated notifications for the authenticated user."""
    assert isinstance(current_user.id, int),"User Id can't be None"
    return await get_user_notifications(
        db, current_user.id, unread_only=unread_only, skip=skip, limit=limit
    )


@router.post(
    "/",
    response_model=NotificationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create notification (superuser)",
)
async def create_notification_endpoint(
    data: NotificationCreate,
    current_user: User = Depends(get_current_active_superuser),
    db: AsyncSession = Depends(get_db),
) -> NotificationRead:
    """
    Create a notification for any user.
    The notification is persisted **and** pushed over WebSocket if the
    target user is currently connected.
    """
    notification = await create_notification(db, data, push_ws=True)
    return NotificationRead.model_validate(notification)


@router.patch(
    "/read-all/",
    summary="Mark all notifications as read",
)
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Mark every unread notification for the current user as read."""

    assert isinstance(current_user.id, int),"User Id can't be None"
    count = await mark_all_read(db, current_user.id)
    return {"updated": count}


@router.get(
    "/{notification_id}/",
    response_model=NotificationRead,
    summary="Get a single notification",
)
async def get_notification_endpoint(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NotificationRead:
    assert isinstance(current_user.id, int),"User Id can't be None"
    notification = await get_notification(db, decode_id_or_404(notification_id), current_user.id)
    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return NotificationRead.model_validate(notification)


@router.patch(
    "/{notification_id}/read/",
    response_model=NotificationRead,
    summary="Mark notification as read",
)
async def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NotificationRead:
    """Mark a single notification as read."""

    assert isinstance(current_user.id, int),"User Id can't be None"
    notification = await mark_as_read(db, decode_id_or_404(notification_id), current_user.id)
    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return NotificationRead.model_validate(notification)


@router.delete(
    "/{notification_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a notification",
)
async def delete_notification_endpoint(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a notification belonging to the current user."""
    deleted = await delete_notification(db, decode_id_or_404(notification_id), current_user.id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
