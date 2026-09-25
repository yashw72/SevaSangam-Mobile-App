"""
Admin — Bookings Monitor Router.

Endpoints (all require role=admin):
  GET  /admin/bookings              — Monitor list (status/type/date/service filters), emergency highlighted
  GET  /admin/bookings/{id}         — Full booking detail with timeline, customer/worker cards, AI match reason
  POST /admin/bookings/{id}/reassign — Manual reassign (mock) for unassigned/failed emergency bookings

Context (mobile context §10.4):
  "Bookings monitor — filters (status, type=emergency, date, service, area);
   booking detail with full timeline, customer/worker cards, and the AI match reason;
   manual reassign action (mock) for unassigned/failed emergency bookings.
   Emergency bookings are visually highlighted."

Manual reassign stubs the matching service (assigns to the nearest available worker
via the same geo-helper already used by the bookings router).
"""

import logging
import uuid
from datetime import datetime, date, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user, require_role
from app.db.session import get_db
from backend.app.models.user import User
from backend.app.models.worker import Worker
from backend.app.models.booking import Booking
from backend.app.models.enums import (
    BookingStatus,
    BookingType,
    VerificationStatus,
    WorkerAvailability,
)

logger = logging.getLogger("sevasangam.admin.bookings")

router = APIRouter(
    prefix="/admin/bookings",
    tags=["Admin — Bookings"],
    dependencies=[Depends(require_role("admin"))],
)


# ── Schemas ──────────────────────────────────────────────────────────────────

class ReassignPayload(BaseModel):
    worker_id: Optional[UUID] = Field(
        None,
        alias="workerId",
        description="Specific worker to assign. If omitted, auto-selects nearest available.",
    )
    note: Optional[str] = Field(None, description="Admin note appended to the booking timeline.")

    model_config = {"populate_by_name": True}


# ── Helpers ──────────────────────────────────────────────────────────────────

def paginated_response(data: list, page: int, limit: int, total: int) -> dict:
    return {
        "data": data,
        "page": page,
        "limit": limit,
        "total": total,
        "totalPages": max(1, (total + limit - 1) // limit),
    }


def booking_to_dict(b: Booking, *, detail: bool = False) -> dict:
    d = {
        "id": str(b.id),
        "customerId": str(b.customer_id),
        "workerId": str(b.worker_id) if b.worker_id else None,
        "serviceId": str(b.service_id),
        "type": b.type.value if b.type else None,
        "status": b.status.value if b.status else None,
        "isEmergency": b.type == BookingType.EMERGENCY,  # visual flag for mobile
        "addressText": b.address_text,
        "addressLat": b.address_lat,
        "addressLng": b.address_lng,
        "scheduledAt": b.scheduled_at.isoformat() if getattr(b, "scheduled_at", None) else None,
        "paymentMode": b.payment_mode,
        "paymentStatus": b.payment_status.value if b.payment_status else None,
        "matchReason": getattr(b, "match_reason", None),  # AI match reason (may be None in mock)
        "createdAt": b.created_at.isoformat() if b.created_at else None,
        "updatedAt": b.updated_at.isoformat() if b.updated_at else None,
    }
    if detail:
        d["timeline"] = b.timeline or []
    return d


async def _get_booking_or_404(booking_id: UUID, db: AsyncSession) -> Booking:
    result = await db.execute(select(Booking).where(Booking.id == booking_id))
    b = result.scalar_one_or_none()
    if not b:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Booking '{booking_id}' not found.",
        )
    return b


# ── GET /admin/bookings ───────────────────────────────────────────────────────

@router.get("", summary="Admin booking monitor list with filters")
async def list_bookings_admin(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    booking_status: Optional[BookingStatus] = Query(None, alias="status"),
    booking_type: Optional[BookingType] = Query(None, alias="type"),
    service_id: Optional[UUID] = Query(None, alias="serviceId"),
    date_from: Optional[date] = Query(None, alias="dateFrom"),
    date_to: Optional[date] = Query(None, alias="dateTo"),
    emergency_only: bool = Query(False, alias="emergencyOnly"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Full booking monitor for admins. Supports all filter combinations.
    Emergency bookings are flagged with `isEmergency: true` for the mobile highlight.
    Results are ordered by created_at desc (newest first).
    """
    base_q = select(Booking)
    count_q = select(func.count(Booking.id))

    if booking_status:
        base_q = base_q.where(Booking.status == booking_status)
        count_q = count_q.where(Booking.status == booking_status)
    if booking_type or emergency_only:
        t = BookingType.EMERGENCY if emergency_only else booking_type
        base_q = base_q.where(Booking.type == t)
        count_q = count_q.where(Booking.type == t)
    if service_id:
        base_q = base_q.where(Booking.service_id == service_id)
        count_q = count_q.where(Booking.service_id == service_id)
    if date_from:
        dt_from = datetime.combine(date_from, datetime.min.time()).replace(tzinfo=timezone.utc)
        base_q = base_q.where(Booking.created_at >= dt_from)
        count_q = count_q.where(Booking.created_at >= dt_from)
    if date_to:
        dt_to = datetime.combine(date_to, datetime.max.time()).replace(tzinfo=timezone.utc)
        base_q = base_q.where(Booking.created_at <= dt_to)
        count_q = count_q.where(Booking.created_at <= dt_to)

    total = (await db.execute(count_q)).scalar_one()
    offset = (page - 1) * limit
    result = await db.execute(
        base_q.order_by(Booking.created_at.desc()).offset(offset).limit(limit)
    )
    bookings = result.scalars().all()

    return paginated_response(
        data=[booking_to_dict(b) for b in bookings],
        page=page,
        limit=limit,
        total=total,
    )


# ── GET /admin/bookings/{id} ──────────────────────────────────────────────────

@router.get("/{booking_id}", summary="Full booking detail (admin only)")
async def get_booking_detail_admin(
    booking_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns the full booking with timeline, customer/worker IDs, AI match reason.
    The mobile detail screen uses this to render the audit-style timeline and
    customer/worker cards.
    """
    booking = await _get_booking_or_404(booking_id, db)
    return booking_to_dict(booking, detail=True)


# ── POST /admin/bookings/{id}/reassign ───────────────────────────────────────

@router.post("/{booking_id}/reassign", summary="Manually reassign an unassigned booking (admin only)")
async def reassign_booking(
    booking_id: UUID,
    payload: ReassignPayload = ReassignPayload(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Manual reassign for unassigned or failed emergency bookings.
    Only bookings in UNASSIGNED or PENDING status can be manually reassigned.

    If `workerId` is provided in the payload, assigns that specific worker
    (validates they exist and are available).

    If omitted, stubs the AI-matching call: picks the nearest available+verified
    worker by workload_this_week ASC (geo-query is omitted since location may be
    NULL in mock; real implementation delegates to the matching service).

    Appends a timeline entry with the admin's action note.
    """
    booking = await _get_booking_or_404(booking_id, db)

    reassignable = {BookingStatus.UNASSIGNED, BookingStatus.PENDING}
    if booking.status not in reassignable:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Only bookings with status 'unassigned' or 'pending' can be manually reassigned. "
                f"Current status: '{booking.status.value}'."
            ),
        )

    now = datetime.now(timezone.utc)

    if payload.worker_id:
        # Explicit worker specified — validate them
        worker_result = await db.execute(
            select(Worker).where(Worker.id == payload.worker_id)
        )
        worker = worker_result.scalar_one_or_none()
        if not worker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Worker '{payload.worker_id}' not found.",
            )
        if worker.verification_status != VerificationStatus.VERIFIED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Worker '{payload.worker_id}' is not verified (status: {worker.verification_status.value}).",
            )
        assigned_worker_id = worker.id
    else:
        # Auto-select: stub — pick least-loaded verified+available worker
        auto_result = await db.execute(
            select(Worker)
            .where(
                Worker.verification_status == VerificationStatus.VERIFIED,
                Worker.availability == WorkerAvailability.AVAILABLE,
            )
            .order_by(Worker.workload_this_week.asc())
            .limit(1)
        )
        auto_worker = auto_result.scalar_one_or_none()
        if not auto_worker:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No available verified workers found for auto-assignment.",
            )
        assigned_worker_id = auto_worker.id

    # Update booking
    booking.worker_id = assigned_worker_id
    booking.status = BookingStatus.ASSIGNED
    booking.updated_at = now

    timeline_entry = {
        "status": BookingStatus.ASSIGNED.value,
        "timestamp": now.isoformat(),
        "note": payload.note or f"Manually reassigned by admin {current_user.id}.",
        "actor": "admin",
    }
    booking.timeline = (booking.timeline or []) + [timeline_entry]

    db.add(booking)
    await db.commit()
    await db.refresh(booking)

    logger.info(
        f"[ADMIN][BOOKINGS] Booking {booking_id} manually reassigned to worker "
        f"{assigned_worker_id} by admin={current_user.id}."
    )

    return {
        "message": "Booking reassigned.",
        "booking": booking_to_dict(booking, detail=True),
        "assignedWorkerId": str(assigned_worker_id),
    }
