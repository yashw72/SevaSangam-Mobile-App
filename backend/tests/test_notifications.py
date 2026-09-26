"""
Unit tests for Notifications endpoints (Prompt 9).

Tests:
1. GET /notifications returns only the current user's notifications.
2. GET /notifications with unreadOnly=true filters correctly.
3. GET /notifications with type filter.
4. GET /notifications/unread-count returns correct badge count.
5. PATCH /notifications/{id}/read marks a notification as read.
6. PATCH /notifications/{id}/read on already-read notification is idempotent (200).
7. PATCH /notifications/{id}/read for another user's notification returns 404.
8. PATCH /notifications/read-all marks all unread as read.
9. notify() service helper creates a Notification row with correct fields.
"""

import uuid
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.core.security import get_current_user
from app.db.session import get_db
from backend.app.models.user import User
from backend.app.models.notification import Notification
from backend.app.models.enums import UserRole


@pytest.fixture
def client():
    return TestClient(app)


# ── Factories ─────────────────────────────────────────────────────────────────

def make_user(role=UserRole.CUSTOMER):
    now = datetime.now(timezone.utc)
    return User(
        id=uuid.uuid4(), name="Test User", phone="+919000000000",
        role=role, created_at=now, updated_at=now,
    )


def make_notif(user_id, notif_type="booking_update", read=False, title_key=None):
    now = datetime.now(timezone.utc)
    return Notification(
        id=uuid.uuid4(),
        user_id=user_id,
        type=notif_type,
        title_key=title_key or f"notifications.{notif_type}",
        body=f"Test notification of type {notif_type}",
        read=read,
        created_at=now,
        updated_at=now,
    )


# ── 1. GET /notifications — own notifications only ───────────────────────────

def test_list_notifications_own_only(client):
    user = make_user()
    notif = make_notif(user.id, "booking_update")

    mock_db = AsyncMock()
    count_res = MagicMock(); count_res.scalar_one.return_value = 1
    list_res = MagicMock(); list_res.scalars.return_value.all.return_value = [notif]
    mock_db.execute.side_effect = [count_res, list_res]

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        resp = client.get(f"{settings.API_V1_STR}/notifications")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["page"] == 1
        assert body["data"][0]["userId"] == str(user.id)
        assert body["data"][0]["type"] == "booking_update"
        assert body["data"][0]["read"] is False
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


# ── 2. GET /notifications?unreadOnly=true ────────────────────────────────────

def test_list_notifications_unread_only(client):
    user = make_user()
    unread_notif = make_notif(user.id, "emergency", read=False)

    mock_db = AsyncMock()
    count_res = MagicMock(); count_res.scalar_one.return_value = 1
    list_res = MagicMock(); list_res.scalars.return_value.all.return_value = [unread_notif]
    mock_db.execute.side_effect = [count_res, list_res]

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        resp = client.get(f"{settings.API_V1_STR}/notifications?unreadOnly=true")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) == 1
        assert data[0]["read"] is False
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


# ── 3. GET /notifications?type=verification_result ───────────────────────────

def test_list_notifications_type_filter(client):
    user = make_user()
    notif = make_notif(user.id, "verification_result")

    mock_db = AsyncMock()
    count_res = MagicMock(); count_res.scalar_one.return_value = 1
    list_res = MagicMock(); list_res.scalars.return_value.all.return_value = [notif]
    mock_db.execute.side_effect = [count_res, list_res]

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        resp = client.get(f"{settings.API_V1_STR}/notifications?type=verification_result")
        assert resp.status_code == 200
        assert resp.json()["data"][0]["type"] == "verification_result"
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


# ── 4. GET /notifications/unread-count ───────────────────────────────────────

def test_unread_count(client):
    user = make_user()

    mock_db = AsyncMock()
    count_res = MagicMock(); count_res.scalar_one.return_value = 3
    mock_db.execute.return_value = count_res

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        resp = client.get(f"{settings.API_V1_STR}/notifications/unread-count")
        assert resp.status_code == 200
        assert resp.json()["unreadCount"] == 3
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


# ── 5. PATCH /notifications/{id}/read ────────────────────────────────────────

def test_mark_notification_as_read(client):
    user = make_user()
    notif = make_notif(user.id, "booking_update", read=False)

    mock_db = AsyncMock()
    notif_res = MagicMock(); notif_res.scalar_one_or_none.return_value = notif
    mock_db.execute.return_value = notif_res

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        resp = client.patch(f"{settings.API_V1_STR}/notifications/{notif.id}/read")
        assert resp.status_code == 200
        assert notif.read is True
        assert mock_db.commit.called
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


# ── 6. PATCH mark-read is idempotent ─────────────────────────────────────────

def test_mark_already_read_notification_idempotent(client):
    user = make_user()
    notif = make_notif(user.id, "booking_update", read=True)  # already read

    mock_db = AsyncMock()
    notif_res = MagicMock(); notif_res.scalar_one_or_none.return_value = notif
    mock_db.execute.return_value = notif_res

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        resp = client.patch(f"{settings.API_V1_STR}/notifications/{notif.id}/read")
        assert resp.status_code == 200
        assert resp.json()["read"] is True
        # No commit call needed for already-read
        assert not mock_db.commit.called
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


# ── 7. PATCH mark-read for another user's notification → 404 ─────────────────

def test_mark_read_other_users_notification_returns_404(client):
    user = make_user()
    other_user_id = uuid.uuid4()
    notif = make_notif(other_user_id, "emergency", read=False)  # belongs to other user

    mock_db = AsyncMock()
    notif_res = MagicMock(); notif_res.scalar_one_or_none.return_value = notif
    mock_db.execute.return_value = notif_res

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        resp = client.patch(f"{settings.API_V1_STR}/notifications/{notif.id}/read")
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


# ── 8. PATCH /notifications/read-all ─────────────────────────────────────────

def test_mark_all_as_read(client):
    user = make_user()

    mock_db = AsyncMock()
    # The bulk UPDATE result mock
    update_res = MagicMock(); update_res.rowcount = 5
    mock_db.execute.return_value = update_res

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        resp = client.patch(f"{settings.API_V1_STR}/notifications/read-all")
        assert resp.status_code == 200
        body = resp.json()
        assert body["updatedCount"] == 5
        assert "5" in body["message"]
        assert mock_db.commit.called
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


# ── 9. notify() service helper ────────────────────────────────────────────────

def test_notify_service_creates_row():
    """notify() should add a Notification row to the session."""
    import asyncio
    from app.services.notifications import notify

    mock_db = AsyncMock()
    user_id = uuid.uuid4()

    async def _run():
        return await notify(
            db=mock_db,
            user_id=user_id,
            notif_type="verification_result",
            title_key="notifications.verification.approved",
            body="Your certificate has been approved.",
        )

    notif = asyncio.run(_run())

    assert notif.user_id == user_id
    assert notif.type == "verification_result"
    assert notif.title_key == "notifications.verification.approved"
    assert notif.read is False
    assert mock_db.add.called
