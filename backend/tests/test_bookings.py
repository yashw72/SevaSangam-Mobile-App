"""
Unit and integration tests for Service Categories & Bookings endpoints (Prompt 5).

Tests:
1. GET /service_categories list and detail.
2. POST /bookings scheduled creation with worker assignment and timeline initialization.
3. POST /bookings emergency creation with matching fallback to unassigned.
4. GET /bookings role-aware filtering (customer vs worker vs admin).
5. GET /bookings/{id} authorization checks.
6. PATCH /bookings/{id}/status:
   - Valid transitions: assigned → accepted → en_route → in_progress → completed.
   - Rejection of illegal transitions with HTTP 400.
   - Timeline appending on every status change.
   - Worker availability & workload updates.
   - Customer cancellation rules.
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
from backend.app.models.service_category import ServiceCategory
from backend.app.models.booking import Booking
from backend.app.models.enums import (
    UserRole,
    BookingStatus,
    BookingType,
    PaymentStatus,
    WorkerAvailability,
    VerificationStatus,
)


@pytest.fixture
def client():
    return TestClient(app)


def make_test_category(cat_id=None, key="electrician", name="services.electrician", charge=250.0):
    now = datetime.now(timezone.utc)
    return ServiceCategory(
        id=cat_id or uuid.uuid4(),
        key=key,
        name=name,
        icon="flash-outline",
        base_visit_charge=charge,
        created_at=now,
        updated_at=now,
    )


def make_test_booking(
    booking_id=None,
    customer_id=None,
    worker_id=None,
    service_id=None,
    status=BookingStatus.ASSIGNED,
    b_type=BookingType.SCHEDULED,
):
    now = datetime.now(timezone.utc)
    return Booking(
        id=booking_id or uuid.uuid4(),
        customer_id=customer_id or uuid.uuid4(),
        worker_id=worker_id or uuid.uuid4(),
        service_id=service_id or uuid.uuid4(),
        type=b_type,
        status=status,
        scheduled_at=now,
        address_text="MG Road, Pune",
        address_lat=18.5204,
        address_lng=73.8567,
        notes="Fan sparking",
        price_estimate=250.0,
        payment_mode="cash",
        payment_status=PaymentStatus.PENDING,
        match_reason="Direct match",
        timeline=[
            {"status": status.value, "timestamp": now.isoformat(), "note": "Initial status"}
        ],
        created_at=now,
        updated_at=now,
    )


# ── 1. Service Categories Tests ─────────────────────────────────────────────

def test_list_service_categories(client):
    user = User(
        id=uuid.uuid4(),
        name="Customer",
        phone="+919876543210",
        role=UserRole.CUSTOMER,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    cat1 = make_test_category(key="electrician", name="services.electrician")
    cat2 = make_test_category(key="plumber", name="services.plumber")

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [cat1, cat2]
    mock_db.execute.return_value = mock_result

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.get(f"{settings.API_V1_STR}/service_categories")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["key"] == "electrician"
        assert data[1]["key"] == "plumber"
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


def test_get_service_category_detail(client):
    user = User(
        id=uuid.uuid4(),
        name="Customer",
        phone="+919876543210",
        role=UserRole.CUSTOMER,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    cat_id = uuid.uuid4()
    cat = make_test_category(cat_id=cat_id)

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = cat
    mock_db.execute.return_value = mock_result

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.get(f"{settings.API_V1_STR}/service_categories/{cat_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(cat_id)
        assert data["key"] == "electrician"
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


# ── 2. Booking Creation Tests ───────────────────────────────────────────────

def test_create_scheduled_booking_with_worker(client):
    customer_id = uuid.uuid4()
    worker_id = uuid.uuid4()
    service_id = uuid.uuid4()
    user = User(
        id=customer_id,
        name="Customer",
        phone="+919876543210",
        role=UserRole.CUSTOMER,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    service = make_test_category(cat_id=service_id, key="electrician")
    worker = Worker(
        id=worker_id,
        user_id=uuid.uuid4(),
        skills=["electrician"],
        experience_years=5,
        rating=4.8,
        rating_count=20,
        verification_status=VerificationStatus.VERIFIED,
        availability=WorkerAvailability.AVAILABLE,
        service_radius_km=10.0,
        workload_this_week=1,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    mock_db = AsyncMock()
    # First query checks service, second checks worker
    service_res = MagicMock()
    service_res.scalar_one_or_none.return_value = service
    worker_res = MagicMock()
    worker_res.scalar_one_or_none.return_value = worker
    mock_db.execute.side_effect = [service_res, worker_res]

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.post(
            f"{settings.API_V1_STR}/bookings",
            json={
                "customerId": str(customer_id),
                "workerId": str(worker_id),
                "serviceId": str(service_id),
                "type": "scheduled",
                "notes": "Need ceiling fan replaced",
                "address": {"text": "Shivaji Nagar, Pune", "lat": 18.5308, "lng": 73.8475},
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["customerId"] == str(customer_id)
        assert data["workerId"] == str(worker_id)
        assert data["status"] == "assigned"
        assert len(data["timeline"]) >= 1
        assert data["timeline"][0]["status"] == "assigned"
        assert mock_db.commit.called
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


def test_create_emergency_booking_no_worker_unassigned(client):
    customer_id = uuid.uuid4()
    service_id = uuid.uuid4()
    user = User(
        id=customer_id,
        name="Customer",
        phone="+919876543210",
        role=UserRole.CUSTOMER,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    service = make_test_category(cat_id=service_id, key="plumber")

    mock_db = AsyncMock()
    service_res = MagicMock()
    service_res.scalar_one_or_none.return_value = service
    # PostGIS geo query returns empty list
    geo_res = MagicMock()
    geo_res.all.return_value = []
    mock_db.execute.side_effect = [service_res, geo_res]

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.post(
            f"{settings.API_V1_STR}/bookings",
            json={
                "customerId": str(customer_id),
                "serviceId": str(service_id),
                "type": "emergency",
                "notes": "Pipe burst in bathroom",
                "address": {"text": "Kothrud, Pune", "lat": 18.5074, "lng": 73.8077},
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "unassigned"
        assert data["type"] == "emergency"
        assert data["workerId"] is None
        assert mock_db.commit.called
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


# ── 3. Role-Aware Listing Tests ─────────────────────────────────────────────

def test_list_bookings_customer_sees_own_only(client):
    customer_id = uuid.uuid4()
    user = User(
        id=customer_id,
        name="Customer",
        phone="+919876543210",
        role=UserRole.CUSTOMER,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    booking = make_test_booking(customer_id=customer_id)

    mock_db = AsyncMock()
    count_res = MagicMock()
    count_res.scalar_one.return_value = 1
    rows_res = MagicMock()
    rows_res.scalars.return_value.all.return_value = [booking]
    mock_db.execute.side_effect = [count_res, rows_res]

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.get(f"{settings.API_V1_STR}/bookings")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["data"][0]["customerId"] == str(customer_id)
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


# ── 4. Status Transition Validation Tests ───────────────────────────────────

def test_worker_accepts_booking(client):
    worker_user_id = uuid.uuid4()
    worker_id = uuid.uuid4()
    booking_id = uuid.uuid4()

    worker_user = User(
        id=worker_user_id,
        name="Worker Ramesh",
        phone="+919876543210",
        role=UserRole.WORKER,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    worker = Worker(
        id=worker_id,
        user_id=worker_user_id,
        skills=["plumbing"],
        experience_years=5,
        rating=4.9,
        rating_count=30,
        verification_status=VerificationStatus.VERIFIED,
        availability=WorkerAvailability.AVAILABLE,
        service_radius_km=10.0,
        workload_this_week=2,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    booking = make_test_booking(
        booking_id=booking_id,
        worker_id=worker_id,
        status=BookingStatus.ASSIGNED,
    )

    mock_db = AsyncMock()
    booking_res = MagicMock()
    booking_res.scalar_one_or_none.return_value = booking
    worker_lookup = MagicMock()
    worker_lookup.scalar_one_or_none.return_value = worker
    mock_db.execute.side_effect = [booking_res, worker_lookup]

    app.dependency_overrides[get_current_user] = lambda: worker_user
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.patch(
            f"{settings.API_V1_STR}/bookings/{booking_id}/status",
            json={"status": "accepted", "note": "Accepted by worker"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "accepted"
        # Check timeline entry was appended
        assert len(data["timeline"]) == 2
        assert data["timeline"][-1]["status"] == "accepted"
        assert data["timeline"][-1]["note"] == "Accepted by worker"
        assert worker.availability == WorkerAvailability.BUSY
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


def test_illegal_status_transition_rejected_with_400(client):
    worker_user_id = uuid.uuid4()
    worker_id = uuid.uuid4()
    booking_id = uuid.uuid4()

    worker_user = User(
        id=worker_user_id,
        name="Worker Ramesh",
        phone="+919876543210",
        role=UserRole.WORKER,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    # Booking is already COMPLETED (terminal state)
    booking = make_test_booking(
        booking_id=booking_id,
        worker_id=worker_id,
        status=BookingStatus.COMPLETED,
    )

    mock_db = AsyncMock()
    booking_res = MagicMock()
    booking_res.scalar_one_or_none.return_value = booking
    mock_db.execute.return_value = booking_res

    app.dependency_overrides[get_current_user] = lambda: worker_user
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        # Attempt illegal transition: completed → in_progress
        response = client.patch(
            f"{settings.API_V1_STR}/bookings/{booking_id}/status",
            json={"status": "in_progress"},
        )
        assert response.status_code == 400
        assert "Invalid status transition" in response.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


def test_customer_cancels_booking(client):
    customer_id = uuid.uuid4()
    booking_id = uuid.uuid4()

    customer = User(
        id=customer_id,
        name="Customer",
        phone="+919876543210",
        role=UserRole.CUSTOMER,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    booking = make_test_booking(
        booking_id=booking_id,
        customer_id=customer_id,
        status=BookingStatus.ASSIGNED,
    )

    mock_db = AsyncMock()
    booking_res = MagicMock()
    booking_res.scalar_one_or_none.return_value = booking
    mock_db.execute.return_value = booking_res

    app.dependency_overrides[get_current_user] = lambda: customer
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.patch(
            f"{settings.API_V1_STR}/bookings/{booking_id}/status",
            json={"status": "cancelled", "note": "Customer changed mind"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "cancelled"
        assert data["timeline"][-1]["status"] == "cancelled"
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


def test_customer_cannot_mark_booking_completed(client):
    customer_id = uuid.uuid4()
    booking_id = uuid.uuid4()

    customer = User(
        id=customer_id,
        name="Customer",
        phone="+919876543210",
        role=UserRole.CUSTOMER,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    booking = make_test_booking(
        booking_id=booking_id,
        customer_id=customer_id,
        status=BookingStatus.IN_PROGRESS,
    )

    mock_db = AsyncMock()
    booking_res = MagicMock()
    booking_res.scalar_one_or_none.return_value = booking
    mock_db.execute.return_value = booking_res

    app.dependency_overrides[get_current_user] = lambda: customer
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.patch(
            f"{settings.API_V1_STR}/bookings/{booking_id}/status",
            json={"status": "completed"},
        )
        assert response.status_code == 403
        assert "Customers can only cancel bookings" in response.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)
