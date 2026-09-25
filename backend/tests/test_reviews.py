"""
Unit and integration tests for Reviews endpoints (Prompt 6).

Tests:
1. POST /reviews succeeds for a completed booking the customer owns.
2. POST /reviews returns 400 for a non-completed booking.
3. POST /reviews returns 403 when booking belongs to a different customer.
4. POST /reviews returns 409 when a review for that booking already exists.
5. POST /reviews returns 403 when called by a worker (not customer).
6. POST /reviews correctly computes and persists the running-average rating update.
7. GET /workers/{id}/reviews returns paginated list.
8. GET /workers/{id}/reviews returns 404 for an unknown worker.
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
from backend.app.models.review import Review
from backend.app.models.enums import (
    UserRole,
    BookingStatus,
    BookingType,
    PaymentStatus,
    VerificationStatus,
    WorkerAvailability,
    InsuranceStatus,
)


@pytest.fixture
def client():
    return TestClient(app)


def make_customer(customer_id=None):
    now = datetime.now(timezone.utc)
    return User(
        id=customer_id or uuid.uuid4(),
        name="Test Customer",
        phone="+919876543210",
        role=UserRole.CUSTOMER,
        created_at=now,
        updated_at=now,
    )


def make_worker(worker_id=None, rating=4.0, rating_count=5):
    now = datetime.now(timezone.utc)
    return Worker(
        id=worker_id or uuid.uuid4(),
        user_id=uuid.uuid4(),
        skills=["electrician"],
        experience_years=5,
        rating=rating,
        rating_count=rating_count,
        verification_status=VerificationStatus.VERIFIED,
        availability=WorkerAvailability.AVAILABLE,
        service_radius_km=10.0,
        workload_this_week=3,
        insurance_status=InsuranceStatus.ACTIVE,
        created_at=now,
        updated_at=now,
    )


def make_booking(booking_id=None, customer_id=None, worker_id=None, status=BookingStatus.COMPLETED):
    now = datetime.now(timezone.utc)
    return Booking(
        id=booking_id or uuid.uuid4(),
        customer_id=customer_id or uuid.uuid4(),
        worker_id=worker_id or uuid.uuid4(),
        service_id=uuid.uuid4(),
        type=BookingType.SCHEDULED,
        status=status,
        address_text="Pune",
        address_lat=18.52,
        address_lng=73.85,
        payment_mode="cash",
        payment_status=PaymentStatus.PENDING,
        timeline=[],
        created_at=now,
        updated_at=now,
    )


def make_review(booking_id, customer_id, worker_id, stars=5):
    now = datetime.now(timezone.utc)
    return Review(
        id=uuid.uuid4(),
        booking_id=booking_id,
        customer_id=customer_id,
        worker_id=worker_id,
        stars=stars,
        comment="Great work!",
        tags=["punctual"],
        created_at=now,
        updated_at=now,
    )


# ── 1. Successful review creation ────────────────────────────────────────────

def test_create_review_success(client):
    customer_id = uuid.uuid4()
    worker_id = uuid.uuid4()
    booking_id = uuid.uuid4()

    customer = make_customer(customer_id)
    worker = make_worker(worker_id, rating=4.0, rating_count=5)
    booking = make_booking(booking_id, customer_id=customer_id, worker_id=worker_id, status=BookingStatus.COMPLETED)

    mock_db = AsyncMock()
    booking_res = MagicMock(); booking_res.scalar_one_or_none.return_value = booking
    worker_res = MagicMock(); worker_res.scalar_one_or_none.return_value = worker
    existing_res = MagicMock(); existing_res.scalar_one_or_none.return_value = None  # no existing review

    mock_db.execute.side_effect = [booking_res, worker_res, existing_res]

    app.dependency_overrides[get_current_user] = lambda: customer
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.post(
            f"{settings.API_V1_STR}/reviews",
            json={
                "bookingId": str(booking_id),
                "customerId": str(customer_id),
                "workerId": str(worker_id),
                "stars": 5,
                "comment": "Excellent service!",
                "tags": ["punctual", "professional"],
            },
        )
        assert response.status_code == 201, response.json()
        data = response.json()
        assert data["stars"] == 5
        assert data["comment"] == "Excellent service!"
        assert data["bookingId"] == str(booking_id)
        assert data["workerId"] == str(worker_id)
        assert data["customerId"] == str(customer_id)
        assert mock_db.commit.called
        # Check rating was updated: ((4.0 * 5) + 5) / 6 = 25/6 ≈ 4.17
        assert worker.rating == round((4.0 * 5 + 5) / 6, 2)
        assert worker.rating_count == 6
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


# ── 2. Review for non-completed booking ──────────────────────────────────────

def test_create_review_booking_not_completed(client):
    customer_id = uuid.uuid4()
    worker_id = uuid.uuid4()
    booking_id = uuid.uuid4()

    customer = make_customer(customer_id)
    booking = make_booking(booking_id, customer_id=customer_id, worker_id=worker_id, status=BookingStatus.IN_PROGRESS)

    mock_db = AsyncMock()
    booking_res = MagicMock(); booking_res.scalar_one_or_none.return_value = booking
    mock_db.execute.return_value = booking_res

    app.dependency_overrides[get_current_user] = lambda: customer
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.post(
            f"{settings.API_V1_STR}/reviews",
            json={
                "bookingId": str(booking_id),
                "customerId": str(customer_id),
                "workerId": str(worker_id),
                "stars": 4,
            },
        )
        assert response.status_code == 400
        assert "completed bookings" in response.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


# ── 3. Review for another customer's booking ─────────────────────────────────

def test_create_review_not_owners_booking(client):
    customer_id = uuid.uuid4()
    other_customer_id = uuid.uuid4()
    worker_id = uuid.uuid4()
    booking_id = uuid.uuid4()

    # Booking belongs to another customer
    booking = make_booking(booking_id, customer_id=other_customer_id, worker_id=worker_id, status=BookingStatus.COMPLETED)
    customer = make_customer(customer_id)

    mock_db = AsyncMock()
    booking_res = MagicMock(); booking_res.scalar_one_or_none.return_value = booking
    mock_db.execute.return_value = booking_res

    app.dependency_overrides[get_current_user] = lambda: customer
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.post(
            f"{settings.API_V1_STR}/reviews",
            json={
                "bookingId": str(booking_id),
                "customerId": str(customer_id),
                "workerId": str(worker_id),
                "stars": 3,
            },
        )
        assert response.status_code == 403
        assert "own" in response.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


# ── 4. Duplicate review (409) ─────────────────────────────────────────────────

def test_create_review_duplicate_returns_409(client):
    customer_id = uuid.uuid4()
    worker_id = uuid.uuid4()
    booking_id = uuid.uuid4()

    customer = make_customer(customer_id)
    worker = make_worker(worker_id)
    booking = make_booking(booking_id, customer_id=customer_id, worker_id=worker_id, status=BookingStatus.COMPLETED)
    existing_review = make_review(booking_id, customer_id, worker_id)

    mock_db = AsyncMock()
    booking_res = MagicMock(); booking_res.scalar_one_or_none.return_value = booking
    worker_res = MagicMock(); worker_res.scalar_one_or_none.return_value = worker
    existing_res = MagicMock(); existing_res.scalar_one_or_none.return_value = existing_review  # already exists!

    mock_db.execute.side_effect = [booking_res, worker_res, existing_res]

    app.dependency_overrides[get_current_user] = lambda: customer
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.post(
            f"{settings.API_V1_STR}/reviews",
            json={
                "bookingId": str(booking_id),
                "customerId": str(customer_id),
                "workerId": str(worker_id),
                "stars": 5,
            },
        )
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


# ── 5. Worker cannot submit reviews ──────────────────────────────────────────

def test_create_review_worker_forbidden(client):
    now = datetime.now(timezone.utc)
    worker_user = User(
        id=uuid.uuid4(),
        name="Worker Bob",
        phone="+919111111111",
        role=UserRole.WORKER,
        created_at=now,
        updated_at=now,
    )

    app.dependency_overrides[get_current_user] = lambda: worker_user
    app.dependency_overrides[get_db] = lambda: AsyncMock()
    try:
        response = client.post(
            f"{settings.API_V1_STR}/reviews",
            json={
                "bookingId": str(uuid.uuid4()),
                "customerId": str(uuid.uuid4()),
                "workerId": str(uuid.uuid4()),
                "stars": 4,
            },
        )
        assert response.status_code == 403
        assert "customers" in response.json()["detail"].lower()
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


# ── 6. Running-average correctness ───────────────────────────────────────────

def test_rating_running_average_fresh_worker(client):
    """First-ever review: old_count=0, new_rating = stars/1."""
    customer_id = uuid.uuid4()
    worker_id = uuid.uuid4()
    booking_id = uuid.uuid4()

    customer = make_customer(customer_id)
    # Worker has never been rated
    worker = make_worker(worker_id, rating=0.0, rating_count=0)
    booking = make_booking(booking_id, customer_id=customer_id, worker_id=worker_id, status=BookingStatus.COMPLETED)

    mock_db = AsyncMock()
    booking_res = MagicMock(); booking_res.scalar_one_or_none.return_value = booking
    worker_res = MagicMock(); worker_res.scalar_one_or_none.return_value = worker
    existing_res = MagicMock(); existing_res.scalar_one_or_none.return_value = None

    mock_db.execute.side_effect = [booking_res, worker_res, existing_res]

    app.dependency_overrides[get_current_user] = lambda: customer
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.post(
            f"{settings.API_V1_STR}/reviews",
            json={
                "bookingId": str(booking_id),
                "customerId": str(customer_id),
                "workerId": str(worker_id),
                "stars": 4,
            },
        )
        assert response.status_code == 201
        assert worker.rating == 4.0
        assert worker.rating_count == 1
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


# ── 7. GET /workers/{id}/reviews paginated ────────────────────────────────────

def test_list_worker_reviews_paginated(client):
    now = datetime.now(timezone.utc)
    customer = make_customer()
    worker_id = uuid.uuid4()
    worker = make_worker(worker_id)

    booking_id = uuid.uuid4()
    review = make_review(booking_id, customer.id, worker_id, stars=5)

    mock_db = AsyncMock()
    # First execute: worker existence check
    worker_res = MagicMock(); worker_res.scalar_one_or_none.return_value = worker
    # Second execute: count query
    count_res = MagicMock(); count_res.scalar_one.return_value = 1
    # Third execute: reviews list
    reviews_res = MagicMock(); reviews_res.scalars.return_value.all.return_value = [review]

    mock_db.execute.side_effect = [worker_res, count_res, reviews_res]

    app.dependency_overrides[get_current_user] = lambda: customer
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.get(f"{settings.API_V1_STR}/workers/{worker_id}/reviews?page=1&limit=20")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["page"] == 1
        assert len(data["data"]) == 1
        assert data["data"][0]["stars"] == 5
        assert data["data"][0]["workerId"] == str(worker_id)
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


# ── 8. GET /workers/{id}/reviews — unknown worker ─────────────────────────────

def test_list_worker_reviews_unknown_worker(client):
    customer = make_customer()
    unknown_worker_id = uuid.uuid4()

    mock_db = AsyncMock()
    worker_res = MagicMock(); worker_res.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = worker_res

    app.dependency_overrides[get_current_user] = lambda: customer
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.get(f"{settings.API_V1_STR}/workers/{unknown_worker_id}/reviews")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)
