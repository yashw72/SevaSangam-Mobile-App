"""
Notifications Router for SevaSangam API.

Endpoints:
  GET   /notifications              — Paginated list, role-aware (each user sees only their own)
  GET   /notifications/unread-count — Unread badge count (lightweight, no pagination)
  PATCH /notifications/{id}/read    — Mark a single notification as read
  PATCH /notifications/read-all     — Mark ALL unread notifications as read (bulk)

Design notes:
  - Real push (FCM) is out of scope for MVP. Notification rows are created by
    other endpoints via `app.services.notifications.notify()`.
  - Each authenticated user can only access their own notifications (user_id check).
  - Admins follow the same rule: they see only their own notifications, not all users'.
  - Ordering: newest first (created_at DESC) so the mobile list is always fresh.
  - The `read` field drives the mobile badge count; no separate read-receipts table.

i18n:
  The `titleKey` field is an i18n key (e.g. "notifications.booking.assigned").
  The mobile app resolves it via its i18n bundle. The `body` field is an
  English fallback summary.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from backend.app.models.user import User
from backend.app.models.notification import Notification

logger = logging.getLogger("sevasangam.notifications")

router = APIRouter(tags=["Notifications"])


# ── Helpers ──────────────────────────────────────────────────────────────────

def paginated_response(data: list, page: int, limit: int, total: int) -> dict:
    """Standard paginated envelope per mobile contract."""
    return {
        "data": data,
        "page": page,
        "limit": limit,
        "total": total,
        "totalPages": max(1, (total + limit - 1) // limit),
    }


def notif_to_dict(n: Notification) -> dict:
    return {
        "id": str(n.id),
        "userId": str(n.user_id),
        "type": n.type,
        "titleKey": n.title_key,
        "body": n.body,
        "read": n.read,
        "createdAt": n.created_at.isoformat() if n.created_at else None,
        "updatedAt": n.updated_at.isoformat() if n.updated_at else None,
    }


# ── GET /notifications ────────────────────────────────────────────────────────

@router.get(
    "/notifications",
    summary="List notifications for the current user (paginated)",
)
async def list_notifications(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False, alias="unreadOnly",
                              description="If true, return only unread notifications."),
    notif_type: Optional[str] = Query(None, alias="type",
                                      description="Filter by notification type, e.g. 'booking_update'."),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns the authenticated user's own notifications, newest first.
    Supports optional `unreadOnly` and `type` filters for the mobile
    notification tray.
    """
    base_q = select(Notification).where(Notification.user_id == current_user.id)
    count_q = select(func.count(Notification.id)).where(Notification.user_id == current_user.id)

    if unread_only:
        base_q = base_q.where(Notification.read == False)   # noqa: E712
        count_q = count_q.where(Notification.read == False)  # noqa: E712
    if notif_type:
        base_q = base_q.where(Notification.type == notif_type)
        count_q = count_q.where(Notification.type == notif_type)

    total = (await db.execute(count_q)).scalar_one()
    offset = (page - 1) * limit
    result = await db.execute(
        base_q.order_by(Notification.created_at.desc()).offset(offset).limit(limit)
    )
    notifs = result.scalars().all()

    return paginated_response(
        data=[notif_to_dict(n) for n in notifs],
        page=page,
        limit=limit,
        total=total,
    )


# ── GET /notifications/unread-count ──────────────────────────────────────────

@router.get(
    "/notifications/unread-count",
    summary="Get unread notification count (badge)",
)
async def unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Lightweight endpoint for the mobile app to poll and refresh the badge count
    on the notification bell icon. Returns a single integer in a named field to
    avoid ambiguity.
    """
    result = await db.execute(
        select(func.count(Notification.id)).where(
            Notification.user_id == current_user.id,
            Notification.read == False,   # noqa: E712
        )
    )
    count = result.scalar_one()
    return {"unreadCount": count}


# ── PATCH /notifications/{id}/read ────────────────────────────────────────────

@router.patch(
    "/notifications/{notification_id}/read",
    summary="Mark a notification as read",
)
async def mark_as_read(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Marks a single notification as read. Returns 404 if the notification does
    not exist or does not belong to the current user (ownership enforced to
    prevent cross-user reads).
    Idempotent: marking an already-read notification is a no-op (200).
    """
    result = await db.execute(
        select(Notification).where(Notification.id == notification_id)
    )
    notif = result.scalar_one_or_none()

    if not notif or notif.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification '{notification_id}' not found.",
        )

    if notif.read:
        # Already read — idempotent, just return current state
        return notif_to_dict(notif)

    notif.read = True
    notif.updated_at = datetime.now(timezone.utc)
    db.add(notif)
    await db.commit()
    await db.refresh(notif)

    return notif_to_dict(notif)


# ── PATCH /notifications/read-all ────────────────────────────────────────────

@router.patch(
    "/notifications/read-all",
    summary="Mark all unread notifications as read (bulk)",
)
async def mark_all_as_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Bulk marks all of the current user's unread notifications as read.
    Used by the mobile "Mark all read" button in the notification tray.
    Returns the count of notifications updated.
    """
    now = datetime.now(timezone.utc)

    # Use a bulk UPDATE for efficiency (avoids loading every row into Python)
    stmt = (
        update(Notification)
        .where(
            Notification.user_id == current_user.id,
            Notification.read == False,   # noqa: E712
        )
        .values(read=True, updated_at=now)
        .execution_options(synchronize_session="fetch")
    )
    result = await db.execute(stmt)
    await db.commit()

    updated_count = result.rowcount if result.rowcount is not None else 0

    return {
        "message": f"Marked {updated_count} notification(s) as read.",
        "updatedCount": updated_count,
    }
