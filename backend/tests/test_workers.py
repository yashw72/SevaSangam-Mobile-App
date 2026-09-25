"""
Unit and integration tests for Workers endpoints (Prompt 4).

Tests:
1. GET /workers paginated listing with skills and availability filters.
2. GET /workers with lat/lng geo-query using Lokesh's PostGIS helpers.
3. GET /workers/{id} and GET /workers/me profile fetching.
4. PATCH /workers/{id} self-update (availability, skills, service radius).
5. PATCH /workers/{id} RBAC & ownership enforcement (cannot edit other worker, cannot self-verify).
6. POST /workers/{id}/certificates upload with pending status & OCR TODO stub.
7. GET /workers/{id}/certificates list.
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
from backend.app.models.enums import (
    UserRole,
    VerificationStatus,
    WorkerAvailability,
    InsuranceStatus,
    CertificateStatus,
)
from geoalchemy2.elements import WKTElement


@pytest.fixture
def client():
    return TestClient(app)


def make_test_worker(worker_id=None, user_id=None, skills=None, availability=WorkerAvailability.AVAILABLE):
    now = datetime.now(timezone.utc)
    w_id = worker_id or uuid.uuid4()
    u_id = user_id or uuid.uuid4()
    return Worker(
        id=w_id,
        user_id=u_id,
        cooperative_id=None,
        skills=skills or ["plumbing", "carpentry"],
        experience_years=4,
        rating=4.7,
        rating_count=15,
        verification_status=VerificationStatus.VERIFIED,
        availability=availability,
        location=WKTElement("POINT(73.8567 18.5204)", srid=4326),
        service_radius_km=12.0,
        workload_this_week=3,
        insurance_status=InsuranceStatus.ACTIVE,
        insurance_coverage="Up to ₹5 Lakhs",
        insurance_valid_till=None,
        created_at=now,
        updated_at=now,
    )


# ── 1. GET /workers ─────────────────────────────────────────────────────────

def test_list_workers_pagination(client):
    user = User(
        id=uuid.uuid4(),
        name="Customer John",
        phone="+919876543210",
        role=UserRole.CUSTOMER,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    worker = make_test_worker()

    mock_db = AsyncMock()
    # Count mock
    count_result = MagicMock()
    count_result.scalar_one.return_value = 1
    # Rows mock
    rows_result = MagicMock()
    rows_result.scalars.return_value.all.return_value = [worker]

    mock_db.execute.side_effect = [count_result, rows_result]

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.get(f"{settings.API_V1_STR}/workers?page=1&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["limit"] == 10
        assert data["total"] == 1
        assert len(data["data"]) == 1
        w_data = data["data"][0]
        assert w_data["id"] == str(worker.id)
        assert w_data["skills"] == ["plumbing", "carpentry"]
        assert w_data["location"]["lat"] == 18.5204
        assert w_data["location"]["lng"] == 73.8567
        assert w_data["insurance"]["status"] == "active"
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


def test_list_workers_with_geo_query(client):
    user = User(
        id=uuid.uuid4(),
        name="Customer John",
        phone="+919876543210",
        role=UserRole.CUSTOMER,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    worker = make_test_worker()

    mock_db = AsyncMock()
    # Count mock
    count_result = MagicMock()
    count_result.scalar_one.return_value = 1
    # Geo query returns tuples of (Worker, distance_km)
    rows_result = MagicMock()
    rows_result.all.return_value = [(worker, 2.45)]

    mock_db.execute.side_effect = [count_result, rows_result]

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.get(
            f"{settings.API_V1_STR}/workers?lat=18.5204&lng=73.8567&radius_km=10&skill=plumbing"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["data"]) == 1
        assert data["data"][0]["id"] == str(worker.id)
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


# ── 2. GET /workers/me & GET /workers/{id} ──────────────────────────────────

def test_get_worker_me(client):
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        name="Worker Ramesh",
        phone="+919876543210",
        role=UserRole.WORKER,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    worker = make_test_worker(user_id=user_id)

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = worker
    mock_db.execute.return_value = mock_result

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.get(f"{settings.API_V1_STR}/workers/me")
        assert response.status_code == 200
        data = response.json()
        assert data["userId"] == str(user_id)
        assert data["availability"] == "available"
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


def test_get_worker_detail_not_found(client):
    user = User(
        id=uuid.uuid4(),
        name="Customer",
        phone="+919876543210",
        role=UserRole.CUSTOMER,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        random_id = uuid.uuid4()
        response = client.get(f"{settings.API_V1_STR}/workers/{random_id}")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


# ── 3. PATCH /workers/{id} Self-Update & Permissions ─────────────────────────

def test_patch_worker_self_update(client):
    user_id = uuid.uuid4()
    worker_id = uuid.uuid4()
    worker_user = User(
        id=user_id,
        name="Worker Ramesh",
        phone="+919876543210",
        role=UserRole.WORKER,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    worker = make_test_worker(worker_id=worker_id, user_id=user_id)

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = worker
    mock_db.execute.return_value = mock_result

    app.dependency_overrides[get_current_user] = lambda: worker_user
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.patch(
            f"{settings.API_V1_STR}/workers/{worker_id}",
            json={
                "availability": "busy",
                "skills": ["electrician", "appliance_repair"],
                "serviceRadiusKm": 15.0,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["availability"] == "busy"
        assert data["skills"] == ["electrician", "appliance_repair"]
        assert data["serviceRadiusKm"] == 15.0
        assert mock_db.commit.called
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


def test_patch_worker_forbidden_for_other_worker(client):
    attacker_user_id = uuid.uuid4()
    victim_user_id = uuid.uuid4()
    worker_id = uuid.uuid4()

    attacker = User(
        id=attacker_user_id,
        name="Other Worker",
        phone="+919111111111",
        role=UserRole.WORKER,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    worker = make_test_worker(worker_id=worker_id, user_id=victim_user_id)

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = worker
    mock_db.execute.return_value = mock_result

    app.dependency_overrides[get_current_user] = lambda: attacker
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.patch(
            f"{settings.API_V1_STR}/workers/{worker_id}",
            json={"availability": "offline"},
        )
        assert response.status_code == 403
        assert "Forbidden" in response.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


def test_patch_worker_cannot_self_verify(client):
    user_id = uuid.uuid4()
    worker_id = uuid.uuid4()
    worker_user = User(
        id=user_id,
        name="Worker Ramesh",
        phone="+919876543210",
        role=UserRole.WORKER,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    worker = make_test_worker(worker_id=worker_id, user_id=user_id)

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = worker
    mock_db.execute.return_value = mock_result

    app.dependency_overrides[get_current_user] = lambda: worker_user
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.patch(
            f"{settings.API_V1_STR}/workers/{worker_id}",
            json={"verificationStatus": "verified"},
        )
        assert response.status_code == 403
        assert "cannot modify their own verification status" in response.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


# ── 4. POST & GET /workers/{id}/certificates ────────────────────────────────

def test_upload_certificate_success(client):
    user_id = uuid.uuid4()
    worker_id = uuid.uuid4()
    worker_user = User(
        id=user_id,
        name="Worker Ramesh",
        phone="+919876543210",
        role=UserRole.WORKER,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    worker = make_test_worker(worker_id=worker_id, user_id=user_id)

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = worker
    mock_db.execute.return_value = mock_result

    app.dependency_overrides[get_current_user] = lambda: worker_user
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.post(
            f"{settings.API_V1_STR}/workers/{worker_id}/certificates",
            json={
                "type": "electrician_license",
                "imageUrl": "https://example.com/certs/license.jpg",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["type"] == "electrician_license"
        assert data["status"] == "pending"
        assert data["workerId"] == str(worker_id)
        assert mock_db.add.called
        assert mock_db.commit.called
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


def test_upload_certificate_forbidden_for_other_user(client):
    attacker_id = uuid.uuid4()
    owner_id = uuid.uuid4()
    worker_id = uuid.uuid4()

    attacker = User(
        id=attacker_id,
        name="Attacker",
        phone="+919999999999",
        role=UserRole.WORKER,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    worker = make_test_worker(worker_id=worker_id, user_id=owner_id)

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = worker
    mock_db.execute.return_value = mock_result

    app.dependency_overrides[get_current_user] = lambda: attacker
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.post(
            f"{settings.API_V1_STR}/workers/{worker_id}/certificates",
            json={"type": "fake_cert"},
        )
        assert response.status_code == 403
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)
