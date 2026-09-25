"""
Unit and integration tests for Authentication & RBAC (Prompt 2).

Tests:
1. Phone OTP request with normalization & mock OTP code.
2. OTP verification issuing JWT with role claims.
3. Role selection rejecting 'admin' and accepting 'customer' / 'worker'.
4. JWT creation, verification, and RBAC require_role dependency.
"""

import uuid
import pytest
from datetime import datetime, timezone, timedelta
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from app.main import app
from app.core.config import settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    get_current_user,
    require_role,
)
from app.db.session import get_db
from backend.app.models.user import User
from backend.app.models.enums import UserRole, VerificationStatus
from backend.app.models.worker import Worker


@pytest.fixture
def client():
    return TestClient(app)


# ── 1. Request OTP Tests ───────────────────────────────────────────────────

def test_request_otp_valid_phone(client):
    response = client.post(
        f"{settings.API_V1_STR}/auth/request-otp",
        json={"phone": "+919876543210"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["phone"] == "+919876543210"
    assert data["message"] == "OTP sent successfully."
    assert data["mockOtp"] == "123456"
    assert data["expiresIn"] == 300


def test_request_otp_normalizes_10_digit_phone(client):
    response = client.post(
        f"{settings.API_V1_STR}/auth/request-otp",
        json={"phone": "9876543210"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["phone"] == "+919876543210"


def test_request_otp_invalid_phone(client):
    response = client.post(
        f"{settings.API_V1_STR}/auth/request-otp",
        json={"phone": "12345"},
    )
    assert response.status_code == 422


# ── 2. Verify OTP Tests ────────────────────────────────────────────────────

def test_verify_otp_invalid_code(client):
    response = client.post(
        f"{settings.API_V1_STR}/auth/verify-otp",
        json={"phone": "+919876543210", "otp": "000000"},
    )
    assert response.status_code == 400
    assert "Invalid or expired OTP" in response.json()["detail"]


def test_verify_otp_new_user(client):
    # Mock get_db returning no existing user
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.post(
            f"{settings.API_V1_STR}/auth/verify-otp",
            json={"phone": "+919999988888", "otp": "123456"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["isNewUser"] is True
        assert "token" in data
        assert data["tokenType"] == "bearer"
        assert data["role"] is None
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_verify_otp_existing_customer(client):
    user_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    mock_user = User(
        id=user_id,
        name="Aarav Sharma",
        phone="+919876543210",
        role=UserRole.CUSTOMER,
        language="en",
        created_at=now,
        updated_at=now,
    )
    mock_user.worker_profile = None

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user
    mock_db.execute.return_value = mock_result

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.post(
            f"{settings.API_V1_STR}/auth/verify-otp",
            json={"phone": "+919876543210", "otp": "123456"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["isNewUser"] is False
        assert data["role"] == "customer"
        assert data["status"] == "active"
        assert "token" in data
    finally:
        app.dependency_overrides.pop(get_db, None)


# ── 3. Role Selection Tests ────────────────────────────────────────────────

def test_select_role_rejects_admin(client):
    # Generate registration token
    temp_token = create_access_token({"sub": "pending", "phone": "+919876543210", "role": "pending"})

    response = client.post(
        f"{settings.API_V1_STR}/auth/select-role",
        headers={"Authorization": f"Bearer {temp_token}"},
        json={"role": "admin", "name": "Fake Admin"},
    )
    assert response.status_code == 422 or response.status_code == 400
    # Schema validation or endpoint rejects admin self-registration


def test_select_role_creates_customer(client):
    temp_token = create_access_token({"sub": "pending", "phone": "+919876543299", "role": "pending"})

    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.post(
            f"{settings.API_V1_STR}/auth/select-role",
            headers={"Authorization": f"Bearer {temp_token}"},
            json={"role": "customer", "name": "Pooja Sharma", "language": "hi"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "customer"
        assert data["isNewUser"] is False
        assert data["status"] == "active"
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_select_role_creates_worker_with_pending_status(client):
    temp_token = create_access_token({"sub": "pending", "phone": "+919876543288", "role": "pending"})

    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.post(
            f"{settings.API_V1_STR}/auth/select-role",
            headers={"Authorization": f"Bearer {temp_token}"},
            json={"role": "worker", "name": "Ramesh Kumar", "language": "mr"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "worker"
        assert data["status"] == "pending"
    finally:
        app.dependency_overrides.pop(get_db, None)


# ── 4. JWT & RBAC require_role Tests ────────────────────────────────────────

def test_jwt_token_creation_and_decoding():
    payload = {"sub": "test-uuid", "role": "admin", "phone": "+919000000000"}
    token = create_access_token(payload, expires_delta=timedelta(minutes=10))

    decoded = decode_access_token(token)
    assert decoded["sub"] == "test-uuid"
    assert decoded["role"] == "admin"
    assert decoded["phone"] == "+919000000000"
    assert "exp" in decoded


def test_jwt_expired_token_raises_401():
    payload = {"sub": "test-uuid", "role": "customer"}
    expired_token = create_access_token(payload, expires_delta=timedelta(seconds=-10))

    with pytest.raises(HTTPException) as exc_info:
        decode_access_token(expired_token)
    assert exc_info.value.status_code == 401
    assert "expired" in exc_info.value.detail.lower()


@pytest.mark.anyio
async def test_rbac_require_role_admin_allows_admin():
    admin_user = User(name="Admin", phone="+919000000000", role=UserRole.ADMIN)
    checker = require_role("admin")
    result = await checker(current_user=admin_user)
    assert result == admin_user


@pytest.mark.anyio
async def test_rbac_require_role_admin_blocks_customer():
    customer_user = User(name="Customer", phone="+919876543210", role=UserRole.CUSTOMER)
    checker = require_role("admin")
    with pytest.raises(HTTPException) as exc_info:
        await checker(current_user=customer_user)
    assert exc_info.value.status_code == 403
    assert "forbidden" in exc_info.value.detail.lower()


@pytest.mark.anyio
async def test_rbac_require_role_multi_roles():
    worker_user = User(name="Worker", phone="+919123456701", role=UserRole.WORKER)
    checker = require_role("admin", "worker")
    result = await checker(current_user=worker_user)
    assert result == worker_user
