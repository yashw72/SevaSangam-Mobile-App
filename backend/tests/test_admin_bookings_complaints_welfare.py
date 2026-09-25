"""
Unit tests for Admin Bookings, Complaints, and Welfare Programmes endpoints (Prompt 8).

Tests — Admin Bookings:
1. Non-admin denied (403).
2. GET /admin/bookings returns paginated list.
3. GET /admin/bookings/{id} returns detail with timeline.
4. POST /admin/bookings/{id}/reassign with explicit workerId.
5. POST /admin/bookings/{id}/reassign auto-assigns least-loaded worker.
6. POST /admin/bookings/{id}/reassign on non-reassignable status returns 400.

Tests — Admin Complaints:
7. Non-admin denied (403).
8. GET /admin/complaints with status filter.
9. POST start-review: open → in_review.
10. POST start-review on in_review → 400 (invalid transition).
11. POST add-note preserves status.
12. POST resolve: in_review → resolved.
13. POST reject: open → rejected (reason required).
14. POST reject missing reason → 422.
15. POST reject on resolved (terminal) → 400.

Tests — Admin Welfare:
16. Non-admin denied (403).
17. POST create programme returns 201.
18. GET list with type filter.
19. PATCH update programme fields.
20. PATCH closed → active is blocked.
21. DELETE draft programme succeeds (204).
22. DELETE active programme → 400.
23. POST announce active programme (stub).
24. POST announce draft programme → 400.
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
from backend.app.models.booking import Booking
from backend.app.models.complaint import Complaint
from backend.app.models.welfare_program import WelfareProgram
from backend.app.models.enums import (
    UserRole, BookingStatus, BookingType, PaymentStatus,
    VerificationStatus, WorkerAvailability, InsuranceStatus,
    ComplaintStatus, WelfareProgramType, WelfareProgramStatus,
)


@pytest.fixture
def client():
    return TestClient(app)


# ── Factories ─────────────────────────────────────────────────────────────────

def make_admin():
    now = datetime.now(timezone.utc)
    return User(id=uuid.uuid4(), name="Admin", phone="+919000000000",
                role=UserRole.ADMIN, created_at=now, updated_at=now)

def make_customer():
    now = datetime.now(timezone.utc)
    return User(id=uuid.uuid4(), name="Customer", phone="+919111111111",
                role=UserRole.CUSTOMER, created_at=now, updated_at=now)

def make_worker(worker_id=None, verification_status=VerificationStatus.VERIFIED,
                availability=WorkerAvailability.AVAILABLE, workload=2):
    now = datetime.now(timezone.utc)
    return Worker(
        id=worker_id or uuid.uuid4(), user_id=uuid.uuid4(),
        skills=["plumber"], experience_years=3,
        rating=4.0, rating_count=10,
        verification_status=verification_status,
        availability=availability,
        service_radius_km=10.0, workload_this_week=workload,
        insurance_status=InsuranceStatus.ACTIVE,
        created_at=now, updated_at=now,
    )

def make_booking(booking_id=None, booking_status=BookingStatus.UNASSIGNED,
                 booking_type=BookingType.EMERGENCY, worker_id=None):
    now = datetime.now(timezone.utc)
    return Booking(
        id=booking_id or uuid.uuid4(), customer_id=uuid.uuid4(),
        worker_id=worker_id, service_id=uuid.uuid4(),
        type=booking_type, status=booking_status,
        address_text="Pune", address_lat=18.52, address_lng=73.85,
        payment_mode="cash", payment_status=PaymentStatus.PENDING,
        timeline=[], created_at=now, updated_at=now,
    )

def make_complaint(complaint_id=None, complaint_status=ComplaintStatus.OPEN):
    now = datetime.now(timezone.utc)
    return Complaint(
        id=complaint_id or uuid.uuid4(),
        raised_by=uuid.uuid4(), booking_id=uuid.uuid4(), worker_id=uuid.uuid4(),
        category="service_quality", description="Worker was late.",
        status=complaint_status, resolution_note=None,
        created_at=now, updated_at=now,
    )

def make_program(program_id=None, prog_status=WelfareProgramStatus.DRAFT,
                 prog_type=WelfareProgramType.INSURANCE):
    now = datetime.now(timezone.utc)
    return WelfareProgram(
        id=program_id or uuid.uuid4(), title="Health Insurance Scheme",
        description="Coverage for all verified workers.",
        type=prog_type, eligibility="Verified workers only",
        enrolled_count=0, status=prog_status,
        created_at=now, updated_at=now,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Admin Bookings
# ═══════════════════════════════════════════════════════════════════════════════

def test_admin_bookings_non_admin_denied(client):
    app.dependency_overrides[get_current_user] = make_customer
    app.dependency_overrides[get_db] = lambda: AsyncMock()
    try:
        resp = client.get(f"{settings.API_V1_STR}/admin/bookings")
        assert resp.status_code == 403
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


def test_admin_list_bookings_paginated(client):
    admin = make_admin()
    booking = make_booking(booking_status=BookingStatus.COMPLETED, booking_type=BookingType.SCHEDULED)

    mock_db = AsyncMock()
    count_res = MagicMock(); count_res.scalar_one.return_value = 1
    bookings_res = MagicMock(); bookings_res.scalars.return_value.all.return_value = [booking]
    mock_db.execute.side_effect = [count_res, bookings_res]

    app.dependency_overrides[get_current_user] = lambda: admin
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        resp = client.get(f"{settings.API_V1_STR}/admin/bookings")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["data"][0]["isEmergency"] is False
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


def test_admin_get_booking_detail(client):
    admin = make_admin()
    booking = make_booking(booking_status=BookingStatus.UNASSIGNED, booking_type=BookingType.EMERGENCY)

    mock_db = AsyncMock()
    booking_res = MagicMock(); booking_res.scalar_one_or_none.return_value = booking
    mock_db.execute.return_value = booking_res

    app.dependency_overrides[get_current_user] = lambda: admin
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        resp = client.get(f"{settings.API_V1_STR}/admin/bookings/{booking.id}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["isEmergency"] is True
        assert "timeline" in body
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


def test_admin_reassign_explicit_worker(client):
    admin = make_admin()
    worker_id = uuid.uuid4()
    booking = make_booking(booking_status=BookingStatus.UNASSIGNED)
    worker = make_worker(worker_id)

    mock_db = AsyncMock()
    booking_res = MagicMock(); booking_res.scalar_one_or_none.return_value = booking
    worker_res = MagicMock(); worker_res.scalar_one_or_none.return_value = worker
    mock_db.execute.side_effect = [booking_res, worker_res]

    app.dependency_overrides[get_current_user] = lambda: admin
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        resp = client.post(
            f"{settings.API_V1_STR}/admin/bookings/{booking.id}/reassign",
            json={"workerId": str(worker_id), "note": "Manual override."},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["assignedWorkerId"] == str(worker_id)
        assert booking.status == BookingStatus.ASSIGNED
        # Timeline entry added
        assert len(booking.timeline) == 1
        assert booking.timeline[0]["actor"] == "admin"
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


def test_admin_reassign_auto_assigns_least_loaded(client):
    admin = make_admin()
    booking = make_booking(booking_status=BookingStatus.PENDING)
    auto_worker = make_worker(workload=1)

    mock_db = AsyncMock()
    booking_res = MagicMock(); booking_res.scalar_one_or_none.return_value = booking
    auto_res = MagicMock(); auto_res.scalar_one_or_none.return_value = auto_worker
    mock_db.execute.side_effect = [booking_res, auto_res]

    app.dependency_overrides[get_current_user] = lambda: admin
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        resp = client.post(
            f"{settings.API_V1_STR}/admin/bookings/{booking.id}/reassign",
            json={},
        )
        assert resp.status_code == 200
        assert resp.json()["assignedWorkerId"] == str(auto_worker.id)
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


def test_admin_reassign_non_reassignable_status(client):
    admin = make_admin()
    booking = make_booking(booking_status=BookingStatus.COMPLETED)

    mock_db = AsyncMock()
    booking_res = MagicMock(); booking_res.scalar_one_or_none.return_value = booking
    mock_db.execute.return_value = booking_res

    app.dependency_overrides[get_current_user] = lambda: admin
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        resp = client.post(
            f"{settings.API_V1_STR}/admin/bookings/{booking.id}/reassign", json={}
        )
        assert resp.status_code == 400
        assert "manually reassigned" in resp.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


# ═══════════════════════════════════════════════════════════════════════════════
# Admin Complaints
# ═══════════════════════════════════════════════════════════════════════════════

def test_admin_complaints_non_admin_denied(client):
    app.dependency_overrides[get_current_user] = make_customer
    app.dependency_overrides[get_db] = lambda: AsyncMock()
    try:
        resp = client.get(f"{settings.API_V1_STR}/admin/complaints")
        assert resp.status_code == 403
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


def test_admin_list_complaints_with_status_filter(client):
    admin = make_admin()
    complaint = make_complaint(complaint_status=ComplaintStatus.OPEN)

    mock_db = AsyncMock()
    count_res = MagicMock(); count_res.scalar_one.return_value = 1
    list_res = MagicMock(); list_res.scalars.return_value.all.return_value = [complaint]
    mock_db.execute.side_effect = [count_res, list_res]

    app.dependency_overrides[get_current_user] = lambda: admin
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        resp = client.get(f"{settings.API_V1_STR}/admin/complaints?status=open")
        assert resp.status_code == 200
        assert resp.json()["data"][0]["status"] == "open"
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


def test_admin_start_review(client):
    admin = make_admin()
    complaint = make_complaint(complaint_status=ComplaintStatus.OPEN)

    mock_db = AsyncMock()
    c_res = MagicMock(); c_res.scalar_one_or_none.return_value = complaint
    mock_db.execute.return_value = c_res

    app.dependency_overrides[get_current_user] = lambda: admin
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        resp = client.post(f"{settings.API_V1_STR}/admin/complaints/{complaint.id}/start-review")
        assert resp.status_code == 200
        assert complaint.status == ComplaintStatus.IN_REVIEW
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


def test_admin_start_review_invalid_transition(client):
    admin = make_admin()
    # Already in_review — cannot go to in_review again
    complaint = make_complaint(complaint_status=ComplaintStatus.IN_REVIEW)

    mock_db = AsyncMock()
    c_res = MagicMock(); c_res.scalar_one_or_none.return_value = complaint
    mock_db.execute.return_value = c_res

    app.dependency_overrides[get_current_user] = lambda: admin
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        resp = client.post(f"{settings.API_V1_STR}/admin/complaints/{complaint.id}/start-review")
        assert resp.status_code == 400
        assert "Cannot transition" in resp.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


def test_admin_add_note_preserves_status(client):
    admin = make_admin()
    complaint = make_complaint(complaint_status=ComplaintStatus.IN_REVIEW)

    mock_db = AsyncMock()
    c_res = MagicMock(); c_res.scalar_one_or_none.return_value = complaint
    mock_db.execute.return_value = c_res

    app.dependency_overrides[get_current_user] = lambda: admin
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        resp = client.post(
            f"{settings.API_V1_STR}/admin/complaints/{complaint.id}/add-note",
            json={"note": "Reached out to worker."},
        )
        assert resp.status_code == 200
        assert complaint.status == ComplaintStatus.IN_REVIEW  # unchanged
        assert complaint.resolution_note == "Reached out to worker."
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


def test_admin_resolve_complaint(client):
    admin = make_admin()
    complaint = make_complaint(complaint_status=ComplaintStatus.IN_REVIEW)

    mock_db = AsyncMock()
    c_res = MagicMock(); c_res.scalar_one_or_none.return_value = complaint
    mock_db.execute.return_value = c_res

    app.dependency_overrides[get_current_user] = lambda: admin
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        resp = client.post(
            f"{settings.API_V1_STR}/admin/complaints/{complaint.id}/resolve",
            json={"note": "Issue verified and compensated."},
        )
        assert resp.status_code == 200
        assert complaint.status == ComplaintStatus.RESOLVED
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


def test_admin_reject_complaint_requires_reason(client):
    admin = make_admin()
    app.dependency_overrides[get_current_user] = lambda: admin
    app.dependency_overrides[get_db] = lambda: AsyncMock()
    try:
        resp = client.post(
            f"{settings.API_V1_STR}/admin/complaints/{uuid.uuid4()}/reject",
            json={},  # reason missing
        )
        assert resp.status_code == 422
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


def test_admin_reject_complaint_open(client):
    admin = make_admin()
    complaint = make_complaint(complaint_status=ComplaintStatus.OPEN)

    mock_db = AsyncMock()
    c_res = MagicMock(); c_res.scalar_one_or_none.return_value = complaint
    mock_db.execute.return_value = c_res

    app.dependency_overrides[get_current_user] = lambda: admin
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        resp = client.post(
            f"{settings.API_V1_STR}/admin/complaints/{complaint.id}/reject",
            json={"reason": "Complaint lacks evidence."},
        )
        assert resp.status_code == 200
        assert complaint.status == ComplaintStatus.REJECTED
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


def test_admin_reject_resolved_complaint_blocked(client):
    admin = make_admin()
    complaint = make_complaint(complaint_status=ComplaintStatus.RESOLVED)  # terminal

    mock_db = AsyncMock()
    c_res = MagicMock(); c_res.scalar_one_or_none.return_value = complaint
    mock_db.execute.return_value = c_res

    app.dependency_overrides[get_current_user] = lambda: admin
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        resp = client.post(
            f"{settings.API_V1_STR}/admin/complaints/{complaint.id}/reject",
            json={"reason": "Trying to reject resolved."},
        )
        assert resp.status_code == 400
        assert "terminal" in resp.json()["detail"].lower() or "Cannot transition" in resp.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


# ═══════════════════════════════════════════════════════════════════════════════
# Admin Welfare
# ═══════════════════════════════════════════════════════════════════════════════

def test_admin_welfare_non_admin_denied(client):
    app.dependency_overrides[get_current_user] = make_customer
    app.dependency_overrides[get_db] = lambda: AsyncMock()
    try:
        resp = client.get(f"{settings.API_V1_STR}/admin/welfare")
        assert resp.status_code == 403
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


def test_admin_create_welfare_program(client):
    admin = make_admin()

    mock_db = AsyncMock()
    app.dependency_overrides[get_current_user] = lambda: admin
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        resp = client.post(
            f"{settings.API_V1_STR}/admin/welfare",
            json={
                "title": "Health Camp 2026",
                "type": "health",
                "status": "draft",
                "eligibility": "All verified workers",
            },
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["title"] == "Health Camp 2026"
        assert body["status"] == "draft"
        assert body["enrolledCount"] == 0
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


def test_admin_list_welfare_with_type_filter(client):
    admin = make_admin()
    program = make_program(prog_type=WelfareProgramType.HEALTH, prog_status=WelfareProgramStatus.ACTIVE)

    mock_db = AsyncMock()
    count_res = MagicMock(); count_res.scalar_one.return_value = 1
    list_res = MagicMock(); list_res.scalars.return_value.all.return_value = [program]
    mock_db.execute.side_effect = [count_res, list_res]

    app.dependency_overrides[get_current_user] = lambda: admin
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        resp = client.get(f"{settings.API_V1_STR}/admin/welfare?type=health")
        assert resp.status_code == 200
        assert resp.json()["data"][0]["type"] == "health"
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


def test_admin_update_welfare_program(client):
    admin = make_admin()
    program = make_program(prog_status=WelfareProgramStatus.DRAFT)

    mock_db = AsyncMock()
    p_res = MagicMock(); p_res.scalar_one_or_none.return_value = program
    mock_db.execute.return_value = p_res

    app.dependency_overrides[get_current_user] = lambda: admin
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        resp = client.patch(
            f"{settings.API_V1_STR}/admin/welfare/{program.id}",
            json={"title": "Updated Title", "status": "active"},
        )
        assert resp.status_code == 200
        assert program.title == "Updated Title"
        assert program.status == WelfareProgramStatus.ACTIVE
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


def test_admin_reopen_closed_program_blocked(client):
    admin = make_admin()
    program = make_program(prog_status=WelfareProgramStatus.CLOSED)

    mock_db = AsyncMock()
    p_res = MagicMock(); p_res.scalar_one_or_none.return_value = program
    mock_db.execute.return_value = p_res

    app.dependency_overrides[get_current_user] = lambda: admin
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        resp = client.patch(
            f"{settings.API_V1_STR}/admin/welfare/{program.id}",
            json={"status": "active"},
        )
        assert resp.status_code == 400
        assert "re-opened" in resp.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


def test_admin_delete_draft_program(client):
    admin = make_admin()
    program = make_program(prog_status=WelfareProgramStatus.DRAFT)

    mock_db = AsyncMock()
    p_res = MagicMock(); p_res.scalar_one_or_none.return_value = program
    mock_db.execute.return_value = p_res

    app.dependency_overrides[get_current_user] = lambda: admin
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        resp = client.delete(f"{settings.API_V1_STR}/admin/welfare/{program.id}")
        assert resp.status_code == 204
        assert mock_db.delete.called
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


def test_admin_delete_active_program_blocked(client):
    admin = make_admin()
    program = make_program(prog_status=WelfareProgramStatus.ACTIVE)

    mock_db = AsyncMock()
    p_res = MagicMock(); p_res.scalar_one_or_none.return_value = program
    mock_db.execute.return_value = p_res

    app.dependency_overrides[get_current_user] = lambda: admin
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        resp = client.delete(f"{settings.API_V1_STR}/admin/welfare/{program.id}")
        assert resp.status_code == 400
        assert "draft" in resp.json()["detail"].lower()
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


def test_admin_announce_active_program(client):
    admin = make_admin()
    program = make_program(prog_status=WelfareProgramStatus.ACTIVE)

    mock_db = AsyncMock()
    p_res = MagicMock(); p_res.scalar_one_or_none.return_value = program
    mock_db.execute.return_value = p_res

    app.dependency_overrides[get_current_user] = lambda: admin
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        resp = client.post(
            f"{settings.API_V1_STR}/admin/welfare/{program.id}/announce",
            json={"message": "Great news for all workers!"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["notificationStatus"] == "stub_logged"
        assert body["announcementText"] == "Great news for all workers!"
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


def test_admin_announce_draft_program_blocked(client):
    admin = make_admin()
    program = make_program(prog_status=WelfareProgramStatus.DRAFT)

    mock_db = AsyncMock()
    p_res = MagicMock(); p_res.scalar_one_or_none.return_value = program
    mock_db.execute.return_value = p_res

    app.dependency_overrides[get_current_user] = lambda: admin
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        resp = client.post(
            f"{settings.API_V1_STR}/admin/welfare/{program.id}/announce", json={}
        )
        assert resp.status_code == 400
        assert "active" in resp.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)
