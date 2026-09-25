"""
Authentication Router for SevaSangam API.

Implements Phone OTP request & verification, JWT issuance,
and Role Selection (Customer / Worker only — Admin cannot be self-registered).
"""

import logging
import uuid
from typing import Dict, Optional
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Header, Security, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    get_current_user,
    security_scheme,
)
from app.db.session import get_db
from backend.app.models.user import User
from backend.app.models.worker import Worker
from backend.app.models.enums import UserRole, VerificationStatus, WorkerAvailability
from app.schemas.auth import (
    RequestOtpRequest,
    RequestOtpResponse,
    VerifyOtpRequest,
    AuthTokenResponse,
    SelectRoleRequest,
)
from app.schemas.user import UserResponse

logger = logging.getLogger("sevasangam.auth")

router = APIRouter(prefix="/auth", tags=["Authentication"])

# In-memory OTP store for active codes (phone -> {otp, expires_at})
_otp_cache: Dict[str, Dict] = {}


@router.post(
    "/request-otp",
    response_model=RequestOtpResponse,
    summary="Request a 6-digit phone OTP",
)
async def request_otp(payload: RequestOtpRequest):
    """
    Accepts an Indian mobile number.
    In development/mock mode: generates/uses fixed OTP '123456' and logs it
    to stdout instead of calling Twilio.
    """
    phone = payload.phone
    otp_code = settings.MOCK_OTP_CODE if settings.MOCK_OTP_ENABLED else "123456"

    # Store in local memory cache with 5-minute expiry
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
    _otp_cache[phone] = {
        "otp": otp_code,
        "expires_at": expires_at,
    }

    # Log instead of calling Twilio in dev/mock mode
    logger.info(f"[AUTH OTP] Sent mock OTP '{otp_code}' to phone: {phone}")

    return RequestOtpResponse(
        message="OTP sent successfully.",
        phone=phone,
        mockOtp=otp_code if settings.MOCK_OTP_ENABLED else None,
        expiresIn=300,
    )


@router.post(
    "/verify-otp",
    response_model=AuthTokenResponse,
    summary="Verify OTP and issue JWT access token",
)
async def verify_otp(
    payload: VerifyOtpRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Verifies the submitted OTP code.
    If the user exists, issues a signed JWT containing user ID and role claims.
    If the user is new (unregistered), issues a temporary registration JWT
    with isNewUser=True so they proceed to role selection.
    """
    phone = payload.phone
    otp = payload.otp.strip()

    # Validate OTP against mock code or memory cache
    is_valid_otp = False
    if settings.MOCK_OTP_ENABLED and otp == settings.MOCK_OTP_CODE:
        is_valid_otp = True
    elif phone in _otp_cache:
        cached = _otp_cache[phone]
        if datetime.now(timezone.utc) <= cached["expires_at"] and cached["otp"] == otp:
            is_valid_otp = True

    if not is_valid_otp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP code. Please try again.",
        )

    # Clear OTP from memory once validated
    _otp_cache.pop(phone, None)

    # Check if user already exists in DB
    result = await db.execute(
        select(User).options(selectinload(User.worker_profile)).where(User.phone == phone)
    )
    user = result.scalar_one_or_none()

    if user:
        # Existing user: compute status and issue standard JWT
        worker_status = None
        if user.role == UserRole.WORKER and user.worker_profile:
            worker_status = user.worker_profile.verification_status.value

        token = create_access_token(
            data={
                "sub": str(user.id),
                "role": user.role.value,
                "phone": user.phone,
                "name": user.name,
            }
        )

        return AuthTokenResponse(
            token=token,
            tokenType="bearer",
            isNewUser=False,
            role=user.role.value,
            status=worker_status or "active",
            user=UserResponse.model_validate(user),
        )
    else:
        # New user: issue temporary registration token
        temp_token = create_access_token(
            data={
                "sub": "pending_registration",
                "phone": phone,
                "role": "pending",
            },
            expires_delta=timedelta(minutes=30),
        )

        return AuthTokenResponse(
            token=temp_token,
            tokenType="bearer",
            isNewUser=True,
            role=None,
            status=None,
            user=None,
        )


@router.post(
    "/select-role",
    response_model=AuthTokenResponse,
    summary="Select user role upon first-time registration",
)
async def select_role(
    payload: SelectRoleRequest,
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Finalizes registration by selecting role: 'customer' or 'worker'.
    Strict rule: Admin accounts can NEVER be self-registered here.
    """
    # 1. Enforce admin restriction
    chosen_role = payload.role.strip().lower()
    if chosen_role == "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin accounts cannot be self-registered. They must be pre-provisioned by the cooperative.",
        )

    if chosen_role not in (UserRole.CUSTOMER.value, UserRole.WORKER.value):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role. Must be 'customer' or 'worker'.",
        )

    # 2. Extract token from header
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required to complete registration.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    raw_token = authorization.split("Bearer ")[1].strip()
    token_payload = decode_access_token(raw_token)

    phone = token_payload.get("phone")
    if not phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token missing phone verification claim.",
        )

    # 3. Check if user exists or create new one
    result = await db.execute(
        select(User).options(selectinload(User.worker_profile)).where(User.phone == phone)
    )
    user = result.scalar_one_or_none()

    target_role_enum = UserRole.CUSTOMER if chosen_role == "customer" else UserRole.WORKER

    if user:
        # Update existing user role & name
        user.name = payload.name
        user.role = target_role_enum
        if payload.language:
            user.language = payload.language
    else:
        now = datetime.now(timezone.utc)
        user = User(
            id=uuid.uuid4(),
            name=payload.name,
            phone=phone,
            role=target_role_enum,
            language=payload.language or "en",
            created_at=now,
            updated_at=now,
        )
        db.add(user)
        await db.flush()

    worker_status = None

    # If chosen role is worker, create/ensure worker profile exists
    if target_role_enum == UserRole.WORKER:
        worker_result = await db.execute(select(Worker).where(Worker.user_id == user.id))
        worker = worker_result.scalar_one_or_none()

        if not worker:
            worker = Worker(
                id=uuid.uuid4(),
                user_id=user.id,
                skills=[],
                experience_years=0,
                rating=0.0,
                rating_count=0,
                verification_status=VerificationStatus.PENDING,
                availability=WorkerAvailability.OFFLINE,
                service_radius_km=10.0,
                workload_this_week=0,
            )
            db.add(worker)
            await db.flush()

        worker_status = worker.verification_status.value

    await db.commit()

    # 4. Issue full authenticated JWT
    new_token = create_access_token(
        data={
            "sub": str(user.id),
            "role": user.role.value,
            "phone": user.phone,
            "name": user.name,
        }
    )

    return AuthTokenResponse(
        token=new_token,
        tokenType="bearer",
        isNewUser=False,
        role=user.role.value,
        status=worker_status or "active",
        user=UserResponse.model_validate(user),
    )


@router.get(
    "/me",
    response_model=AuthTokenResponse,
    summary="Get current user details and verification status",
)
async def get_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns the currently authenticated user's profile and worker status (if applicable).
    """
    worker_status = None
    if current_user.role == UserRole.WORKER:
        worker_result = await db.execute(
            select(Worker).where(Worker.user_id == current_user.id)
        )
        worker = worker_result.scalar_one_or_none()
        if worker:
            worker_status = worker.verification_status.value

    token = create_access_token(
        data={
            "sub": str(current_user.id),
            "role": current_user.role.value,
            "phone": current_user.phone,
            "name": current_user.name,
        }
    )

    return AuthTokenResponse(
        token=token,
        tokenType="bearer",
        isNewUser=False,
        role=current_user.role.value,
        status=worker_status or "active",
        user=UserResponse.model_validate(current_user),
    )
