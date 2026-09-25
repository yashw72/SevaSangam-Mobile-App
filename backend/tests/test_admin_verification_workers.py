"""
Unit tests for Admin Verification and Admin Workers endpoints (Prompt 7).

Tests — Verification:
1. Non-admin caller receives 403 on every admin endpoint.
2. GET /admin/verification returns only pending certificates.
3. POST .../approve marks cert as APPROVED and recalculates worker status.
4. POST .../approve on already-approved cert returns 400.
5. POST .../reject requires reason (missing → 422).
6. POST .../reject marks cert REJECTED and worker becomes REJECTED.
7. POST .../request-reupload resets cert to PENDING, worker stays PENDING.

Tests — Workers:
8. GET /admin/workers returns paginated list (admin only).
9. GET /admin/workers/{id} returns detail with recent bookings.
10. POST /admin/workers/{id}/suspend sets verification_status=suspended.
11. POST /admin/workers/{id}/suspend on already-suspended worker → 400.
12. POST /admin/workers/{id}/reactivate sets verification_status=verified.
13. POST /admin/workers/{id}/reactivate on non-suspended worker → 400.
"""

import uuid
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.core.security import get_current_user
from app.db.session import get_db
from backend.app.models.user import User
from backend.app.models.worker import Worker
from backend.app.models.certificate import Certificate
from backend.app.models.booking import Booking
from backend.app.models.enums import (
    UserRole,
    VerificationStatus,
    WorkerAvailability,
    InsuranceStatus,
    CertificateStatus,
    BookingStatus,
    BookingType,
    PaymentStatus,
)


@pytest.fixture
def client():
    return TestClient(app)


def make_admin():
    now = datetime.now(timezone.utc)
    return User(
        id=uuid.uuid4(), name="Admin", phone="+919000000000",
        role=UserRole.ADMIN, created_at=now, updated_at=now,
    )


def make_customer():
    now = datetime.now(timezone.utc)
    return User(
        id=uuid.uuid4(), name="Customer", phone="+919111111111",
        role=UserRole.CUSTOMER, created_at=now, updated_at=now,
    )


def make_worker(worker_id=None, verification_status=VerificationStatus.PENDING):
    now = datetime.now(timezone.utc)
    return Worker(
        id=worker_id or uuid.uuid4(), user_id=uuid.uuid4(),
        skills=["plumber"], experience_years=3,
        rating=4.0, rating_count=10,
        verification_status=verification_status,
        availability=WorkerAvailability.AVAILABLE,
        service_radius_km=10.0, workload_this_week=2,
        insurance_status=InsuranceStatus.ACTIVE,
        created_at=now, updated_at=now,
    )


def make_cert(worker_id=None, cert_status=CertificateStatus.PENDING):
    now = datetime.now(timezone.utc)
    return Certificate(
        id=uuid.uuid4(),
        worker_id=worker_id or uuid.uuid4(),
        type="plumber_license",
        image_url="https://example.com/cert.jpg",
        ocr_text="PLUMBER LICENSE 12345",
        ocr_confidence=0.95,
        status=cert_status,
        review_note=None,
        created_at=now, updated_at=now,
    )


def make_booking(worker_id, booking_status=BookingStatus.COMPLETED):
    now = datetime.now(timezone.utc)
    return Booking(
        id=uuid.uuid4(), customer_id=uuid.uuid4(), worker_id=worker_id,
        service_id=uuid.uuid4(), type=BookingType.SCHEDULED,
        status=booking_status, address_text="Pune",
        address_lat=18.52, address_lng=73.85,
        payment_mode="cash", payment_status=PaymentStatus.PENDING,
        timeline=[], created_at=now, updated_at=now,
    )


# ── Helper to set up DB mock for verification endpoints ─────────────────────

def mock_db_for_cert_action(cert, worker, all_certs=None):
    mock_db = AsyncMock()
    cert_res = MagicMock(); cert_res.scalar_one_or_none.return_value = cert
    worker_res = MagicMock(); worker_res.scalar_one_or_none.return_value = worker
    all_certs_res = MagicMock()
    all_certs_res.scalars.return_value.all.return_value = all_certs or [cert]
    mock_db.execute.side_effect = [cert_res, worker_res, all_certs_res]
    return mock_db


# ═══════════════════════════════════════════════════════════════
# RBAC guard tests — non-admin must be rejected with 403
# ═══════════════════════════════════════════════════════════════

def test_non_admin_verification_queue_denied(client):
    app.dependency_overrides[get_current_user] = make_customer
    app.dependency_overrides[get_db] = lambda: AsyncMock()
    try:
        resp = client.get(f"{settings.API_V1_STR}/admin/verification")
        assert resp.status_code == 403
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


def test_non_admin_suspend_denied(client):
    app.dependency_overrides[get_current_user] = make_customer
    app.dependency_overrides[get_db] = lambda: AsyncMock()
    try:
        resp = client.post(
            f"{settings.API_V1_STR}/admin/workers/{uuid.uuid4()}/suspend",
            json={"reason": "test"},
        )
        assert resp.status_code == 403
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


# ═══════════════════════════════════════════════════════════════
# Verification queue
# ═══════════════════════════════════════════════════════════════

def test_list_pending_certificates(client):
    admin = make_admin()
    worker = make_worker()
    cert = make_cert(worker.id, CertificateStatus.PENDING)

    mock_db = AsyncMock()
    # count query
    count_res = MagicMock(); count_res.scalar_one.return_value = 1
    # certs list
    certs_res = MagicMock(); certs_res.scalars.return_value.all.return_value = [cert]
    # workers batch fetch
    workers_res = MagicMock(); workers_res.scalars.return_value.all.return_value = [worker]
    mock_db.execute.side_effect = [count_res, certs_res, workers_res]

    app.dependency_overrides[get_current_user] = lambda: admin
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        resp = client.get(f"{settings.API_V1_STR}/admin/verification")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["data"][0]["status"] == "pending"
        assert data["data"][0]["worker"]["id"] == str(worker.id)
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


def test_approve_certificate_verifies_worker(client):
    admin = make_admin()
    worker = make_worker(verification_status=VerificationStatus.PENDING)
    cert = make_cert(worker.id, CertificateStatus.PENDING)

    mock_db = mock_db_for_cert_action(cert, worker, all_certs=[cert])
    app.dependency_overrides[get_current_user] = lambda: admin
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        resp = client.post(
            f"{settings.API_V1_STR}/admin/verification/{cert.id}/approve",
            json={"note": "Looks good"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["certificate"]["status"] == "approved"
        # All certs now approved → worker becomes verified
        assert worker.verification_status == VerificationStatus.VERIFIED
        assert body["workerVerificationStatus"] == "verified"
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


def test_approve_already_approved_cert_returns_400(client):
    admin = make_admin()
    worker = make_worker(verification_status=VerificationStatus.VERIFIED)
    cert = make_cert(worker.id, CertificateStatus.APPROVED)  # already approved

    mock_db = AsyncMock()
    cert_res = MagicMock(); cert_res.scalar_one_or_none.return_value = cert
    mock_db.execute.return_value = cert_res

    app.dependency_overrides[get_current_user] = lambda: admin
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        resp = client.post(
            f"{settings.API_V1_STR}/admin/verification/{cert.id}/approve",
            json={},
        )
        assert resp.status_code == 400
        assert "already approved" in resp.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


def test_reject_certificate_requires_reason(client):
    admin = make_admin()
    # Missing reason field → Pydantic returns 422
    app.dependency_overrides[get_current_user] = lambda: admin
    app.dependency_overrides[get_db] = lambda: AsyncMock()
    try:
        resp = client.post(
            f"{settings.API_V1_STR}/admin/verification/{uuid.uuid4()}/reject",
            json={},  # reason missing
        )
        assert resp.status_code == 422
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


def test_reject_certificate_updates_worker_status(client):
    admin = make_admin()
    worker = make_worker(verification_status=VerificationStatus.PENDING)
    cert = make_cert(worker.id, CertificateStatus.PENDING)

    mock_db = mock_db_for_cert_action(cert, worker, all_certs=[cert])
    app.dependency_overrides[get_current_user] = lambda: admin
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        resp = client.post(
            f"{settings.API_V1_STR}/admin/verification/{cert.id}/reject",
            json={"reason": "Image is blurry and illegible."},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["certificate"]["status"] == "rejected"
        assert worker.verification_status == VerificationStatus.REJECTED
        assert body["workerVerificationStatus"] == "rejected"
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


def test_request_reupload_resets_cert_to_pending(client):
    admin = make_admin()
    worker = make_worker(verification_status=VerificationStatus.REJECTED)
    cert = make_cert(worker.id, CertificateStatus.REJECTED)

    mock_db = AsyncMock()
    cert_res = MagicMock(); cert_res.scalar_one_or_none.return_value = cert
    worker_res = MagicMock(); worker_res.scalar_one_or_none.return_value = worker
    mock_db.execute.side_effect = [cert_res, worker_res]

    app.dependency_overrides[get_current_user] = lambda: admin
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        resp = client.post(
            f"{settings.API_V1_STR}/admin/verification/{cert.id}/request-reupload",
            json={"note": "Please upload a clearer scan."},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["certificate"]["status"] == "pending"
        assert worker.verification_status == VerificationStatus.PENDING
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


# ═══════════════════════════════════════════════════════════════
# Admin workers endpoints
# ═══════════════════════════════════════════════════════════════

def test_admin_list_workers_paginated(client):
    admin = make_admin()
    worker = make_worker(verification_status=VerificationStatus.PENDING)

    mock_db = AsyncMock()
    count_res = MagicMock(); count_res.scalar_one.return_value = 1
    workers_res = MagicMock(); workers_res.scalars.return_value.all.return_value = [worker]
    mock_db.execute.side_effect = [count_res, workers_res]

    app.dependency_overrides[get_current_user] = lambda: admin
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        resp = client.get(f"{settings.API_V1_STR}/admin/workers")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["data"][0]["verificationStatus"] == "pending"
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


def test_admin_get_worker_detail_with_bookings(client):
    admin = make_admin()
    worker_id = uuid.uuid4()
    worker = make_worker(worker_id, VerificationStatus.VERIFIED)
    booking = make_booking(worker_id)

    mock_db = AsyncMock()
    worker_res = MagicMock(); worker_res.scalar_one_or_none.return_value = worker
    bookings_res = MagicMock(); bookings_res.scalars.return_value.all.return_value = [booking]
    mock_db.execute.side_effect = [worker_res, bookings_res]

    app.dependency_overrides[get_current_user] = lambda: admin
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        resp = client.get(f"{settings.API_V1_STR}/admin/workers/{worker_id}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == str(worker_id)
        assert len(body["recentBookings"]) == 1
        assert body["recentBookings"][0]["status"] == "completed"
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


def test_suspend_worker(client):
    admin = make_admin()
    worker_id = uuid.uuid4()
    worker = make_worker(worker_id, VerificationStatus.VERIFIED)

    mock_db = AsyncMock()
    worker_res = MagicMock(); worker_res.scalar_one_or_none.return_value = worker
    mock_db.execute.return_value = worker_res

    app.dependency_overrides[get_current_user] = lambda: admin
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        resp = client.post(
            f"{settings.API_V1_STR}/admin/workers/{worker_id}/suspend",
            json={"reason": "Repeated late arrivals and complaints."},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert worker.verification_status == VerificationStatus.SUSPENDED
        assert body["worker"]["verificationStatus"] == "suspended"
        assert "suspensionReason" in body
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


def test_suspend_already_suspended_returns_400(client):
    admin = make_admin()
    worker = make_worker(verification_status=VerificationStatus.SUSPENDED)

    mock_db = AsyncMock()
    worker_res = MagicMock(); worker_res.scalar_one_or_none.return_value = worker
    mock_db.execute.return_value = worker_res

    app.dependency_overrides[get_current_user] = lambda: admin
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        resp = client.post(
            f"{settings.API_V1_STR}/admin/workers/{worker.id}/suspend",
            json={"reason": "Duplicate action."},
        )
        assert resp.status_code == 400
        assert "already suspended" in resp.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


def test_reactivate_worker(client):
    admin = make_admin()
    worker = make_worker(verification_status=VerificationStatus.SUSPENDED)

    mock_db = AsyncMock()
    worker_res = MagicMock(); worker_res.scalar_one_or_none.return_value = worker
    mock_db.execute.return_value = worker_res

    app.dependency_overrides[get_current_user] = lambda: admin
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        resp = client.post(
            f"{settings.API_V1_STR}/admin/workers/{worker.id}/reactivate",
            json={},
        )
        assert resp.status_code == 200
        assert worker.verification_status == VerificationStatus.VERIFIED
        assert resp.json()["worker"]["verificationStatus"] == "verified"
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


def test_reactivate_non_suspended_worker_returns_400(client):
    admin = make_admin()
    worker = make_worker(verification_status=VerificationStatus.VERIFIED)

    mock_db = AsyncMock()
    worker_res = MagicMock(); worker_res.scalar_one_or_none.return_value = worker
    mock_db.execute.return_value = worker_res

    app.dependency_overrides[get_current_user] = lambda: admin
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        resp = client.post(
            f"{settings.API_V1_STR}/admin/workers/{worker.id}/reactivate",
            json={},
        )
        assert resp.status_code == 400
        assert "suspended" in resp.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)
