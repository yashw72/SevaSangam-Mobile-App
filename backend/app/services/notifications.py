"""
Notifications service helper.

Provides `notify()` — a single function any endpoint can await to persist
a Notification row for a user. Real FCM push is out of scope for MVP;
this module is the *only* place that should create Notification rows, so
wiring in FCM later is a one-line change here.

Usage (from any router):
    from app.services.notifications import notify

    await notify(
        db=db,
        user_id=worker.user_id,
        notif_type="booking_update",
        title_key="notifications.booking.assigned",
        body=f"You have been assigned booking #{booking.id}.",
    )
"""

import logging
import uuid
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.notification import Notification

logger = logging.getLogger("sevasangam.notifications")


async def notify(
    *,
    db: AsyncSession,
    user_id: UUID,
    notif_type: str,
    title_key: str,
    body: str | None = None,
) -> Notification:
    """
    Persist a Notification row and (stub) log it instead of sending a real push.

    Args:
        db:          SQLAlchemy async session (already open; caller commits).
        user_id:     Recipient user UUID.
        notif_type:  Short event type string, e.g. "booking_update", "emergency",
                     "verification_result", "welfare_announcement".
        title_key:   i18n key for the mobile app to localise the title,
                     e.g. "notifications.booking.assigned".
        body:        Optional human-readable body text (English fallback).

    Returns:
        The unsaved Notification ORM object. The caller is responsible for
        committing the session (so it stays in the same transaction as the
        triggering event).
    """
    now = datetime.now(timezone.utc)
    notif = Notification(
        id=uuid.uuid4(),
        user_id=user_id,
        type=notif_type,
        title_key=title_key,
        body=body,
        read=False,
        created_at=now,
        updated_at=now,
    )
    db.add(notif)

    # TODO: replace this log with a real FCM dispatch (see mobile context §18).
    logger.info(
        f"[NOTIFY][STUB] user={user_id} type={notif_type!r} "
        f"title_key={title_key!r} body={body!r}"
    )

    return notif
