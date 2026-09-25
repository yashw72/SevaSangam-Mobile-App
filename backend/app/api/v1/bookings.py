"""
Bookings Router for SevaSangam API.

Endpoints:
  POST   /bookings          — Create scheduled or emergency booking with AI worker-matching stub
  GET    /bookings          — List bookings (role-aware: customer sees own, worker sees assigned, filters)
  GET    /bookings/{id}     — Get booking details by ID
  PATCH  /bookings/{id}/status — Update booking status with strict state-transition validation and timeline append
"""

import logging
import uuid
from datetime import datetime, date, timezone
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select, func, and_, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.services.matching import find_best_worker_match
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
)
from app.schemas.booking import (
    BookingResponse,
    BookingCreate,
    AddressSchema,
    TimelineEntry,
)

logger = logging.getLogger("sevasangam.bookings")

router = APIRouter(prefix="/bookings", tags=["Bookings"])


# ── Valid Status Transitions State Machine ──────────────────────────────────
# Per ANTIGRAVITY_MOBILE_CONTEXT.md:
# pending → assigned → accepted → en_route → in_progress → completed
# plus rejected, cancelled, unassigned

VALID_STATUS_TRANSITIONS = {
    BookingStatus.PENDING: {
        BookingStatus.ASSIGNED,
        BookingStatus.ACCEPTED,
        BookingStatus.UNASSIGNED,
        BookingStatus.CANCELLED,
    },
    BookingStatus.ASSIGNED: {
        BookingStatus.ACCEPTED,
        BookingStatus.REJECTED,
        BookingStatus.CANCELLED,
    },
    BookingStatus.ACCEPTED: {
        BookingStatus.EN_ROUTE,
        BookingStatus.IN_PROGRESS,
        BookingStatus.CANCELLED,
    },
    BookingStatus.EN_ROUTE: {
        BookingStatus.IN_PROGRESS,
        BookingStatus.CANCELLED,
    },
    BookingStatus.IN_PROGRESS: {
        BookingStatus.COMPLETED,
        BookingStatus.CANCELLED,
    },
    BookingStatus.REJECTED: {
        BookingStatus.PENDING,
        BookingStatus.ASSIGNED,
        BookingStatus.UNASSIGNED,
        BookingStatus.CANCELLED,
    },
    BookingStatus.UNASSIGNED: {
        BookingStatus.ASSIGNED,
        BookingStatus.CANCELLED,
    },
    BookingStatus.COMPLETED: set(),  # Terminal state
    BookingStatus.CANCELLED: set(),  # Terminal state
}


# ── Schemas ─────────────────────────────────────────────────────────────────

class BookingStatusUpdate(BaseModel):
    status: BookingStatus
    note: Optional[str] = None


# ── Helpers ─────────────────────────────────────────────────────────────────

def paginated_response(data: list, page: int, limit: int, total: int) -> dict:
    return {
        "data": data,
        "page": page,
        "limit": limit,
        "total": total,
        "totalPages": max(1, (total + limit - 1) // limit),
    }


def booking_to_response(b: Booking) -> BookingResponse:
    now = datetime.now(timezone.utc)
    addr = None
    if b.address_text or b.address_lat is not None or b.address_lng is not None:
        addr = AddressSchema(
            text=b.address_text,
            lat=b.address_lat,
            lng=b.address_lng,
        )

    timeline_entries = []
    if b.timeline:
        for t in b.timeline:
            if isinstance(t, dict):
                ts = t.get("timestamp")
                if isinstance(ts, str):
                    try:
                        ts = datetime.fromisoformat(ts)
                    except Exception:
                        ts = now
                elif not isinstance(ts, datetime):
                    ts = now
                timeline_entries.append(
                    TimelineEntry(
                        status=str(t.get("status", "")),
                        timestamp=ts,
                        note=t.get("note"),
                    )
                )
            elif isinstance(t, TimelineEntry):
                timeline_entries.append(t)

    return BookingResponse(
        id=b.id or uuid.uuid4(),
        customer_id=b.customer_id,
        worker_id=b.worker_id,
        service_id=b.service_id,
        type=b.type,
        status=b.status,
        scheduled_at=b.scheduled_at,
        address=addr,
        notes=b.notes,
        price_estimate=b.price_estimate,
        payment_mode=b.payment_mode,
        payment_status=b.payment_status,
        match_reason=b.match_reason,
        timeline=timeline_entries,
        created_at=b.created_at or now,
        updated_at=b.updated_at or now,
    )


# ── POST /bookings ──────────────────────────────────────────────────────────

@router.post(
    "",
    response_model=BookingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new scheduled or emergency booking",
)
async def create_booking(
    payload: BookingCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Creates a booking for the customer.
    - If customerId is provided, verifies user is admin or the customer themselves.
    - If workerId is omitted, calls the matching service to locate the nearest available worker.
    - Emergency bookings with no match transition to 'unassigned'.
    - Starts the booking timeline with an initial creation record.
    """
    # Enforce customer ownership
    customer_id = payload.customer_id or current_user.id
    if current_user.role != UserRole.ADMIN and current_user.id != customer_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You can only create bookings for your own account.",
        )

    # Validate Service Category
    service_result = await db.execute(
        select(ServiceCategory).where(ServiceCategory.id == payload.service_id)
    )
    service = service_result.scalar_one_or_none()
    if not service:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid serviceId '{payload.service_id}'. Service category not found.",
        )

    now = datetime.now(timezone.utc)
    worker_id: Optional[UUID] = payload.worker_id
    match_reason: Optional[str] = None
    initial_status: BookingStatus = BookingStatus.PENDING

    # If worker is directly selected
    if worker_id is not None:
        worker_res = await db.execute(
            select(Worker).where(Worker.id == worker_id)
        )
        if not worker_res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Worker with id '{worker_id}' does not exist.",
            )
        initial_status = BookingStatus.ASSIGNED
        match_reason = "Directly selected by customer"
    else:
        # Auto-match using matching service
        lat = payload.address.lat if payload.address else None
        lng = payload.address.lng if payload.address else None

        if lat is not None and lng is not None:
            # Query nearest available worker with service key as skill
            matched_worker, reason = await find_best_worker_match(
                db=db,
                lat=lat,
                lng=lng,
                skill=service.key,
                radius_km=15.0,
            )
            if matched_worker:
                worker_id = matched_worker.id
                match_reason = reason
                initial_status = BookingStatus.ASSIGNED
            else:
                if payload.type == BookingType.EMERGENCY:
                    initial_status = BookingStatus.UNASSIGNED
                    match_reason = "No available workers found nearby"
                else:
                    initial_status = BookingStatus.PENDING
                    match_reason = "Pending worker assignment"
        else:
            initial_status = BookingStatus.PENDING
            match_reason = "Pending location for worker assignment"

    # Price estimate default
    price_estimate = payload.price_estimate
    if price_estimate is None or price_estimate == 0:
        price_estimate = service.base_visit_charge

    # Initialize timeline
    timeline = [
        {
            "status": initial_status.value,
            "timestamp": now.isoformat(),
            "note": "Booking created" + (f": {match_reason}" if match_reason else ""),
        }
    ]

    booking = Booking(
        id=uuid.uuid4(),
        customer_id=customer_id,
        worker_id=worker_id,
        service_id=payload.service_id,
        type=payload.type,
        status=initial_status,
        scheduled_at=payload.scheduled_at,
        address_text=payload.address.text if payload.address else None,
        address_lat=payload.address.lat if payload.address else None,
        address_lng=payload.address.lng if payload.address else None,
        notes=payload.notes,
        price_estimate=price_estimate,
        payment_mode=payload.payment_mode or "cash",
        payment_status=PaymentStatus.PENDING,
        match_reason=match_reason,
        timeline=timeline,
        created_at=now,
        updated_at=now,
    )

    db.add(booking)
    await db.commit()
    await db.refresh(booking)

    logger.info(
        f"[BOOKINGS] Created booking {booking.id} ({booking.type.value}) for customer {customer_id}. "
        f"Status: {booking.status.value}, Worker: {worker_id}"
    )

    return booking_to_response(booking)


# ── GET /bookings ───────────────────────────────────────────────────────────

@router.get(
    "",
    summary="List bookings (role-aware)",
)
async def list_bookings(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status (e.g. pending, in_progress, completed)"),
    type: Optional[str] = Query(None, description="Filter by booking type: scheduled, emergency"),
    date_filter: Optional[date] = Query(None, alias="date", description="Filter by scheduled/created date (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns a paginated list of bookings.
    - Customer role: returns only bookings owned by the caller.
    - Worker role: returns bookings assigned to this worker.
    - Admin role: returns all bookings across the platform.
    Supports status, type, and date filters.
    """
    query = select(Booking)
    count_query = select(func.count(Booking.id))
    conditions = []

    # Role-aware scoping
    if current_user.role == UserRole.CUSTOMER:
        conditions.append(Booking.customer_id == current_user.id)
    elif current_user.role == UserRole.WORKER:
        # Find worker record
        worker_res = await db.execute(
            select(Worker.id).where(Worker.user_id == current_user.id)
        )
        worker_row = worker_res.scalar_one_or_none()
        if not worker_row:
            return paginated_response(data=[], page=page, limit=limit, total=0)
        conditions.append(Booking.worker_id == worker_row)
    # Admin has no role condition

    # Apply status filter
    if status:
        try:
            status_enum = BookingStatus(status.strip().lower())
            conditions.append(Booking.status == status_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status '{status}'.",
            )

    # Apply type filter
    if type:
        try:
            type_enum = BookingType(type.strip().lower())
            conditions.append(Booking.type == type_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid booking type '{type}'.",
            )

    # Apply date filter
    if date_filter:
        # Match either scheduled_at or created_at
        date_cond = (
            cast(Booking.scheduled_at, Date) == date_filter
        ) | (cast(Booking.created_at, Date) == date_filter)
        conditions.append(date_cond)

    if conditions:
        query = query.where(and_(*conditions))
        count_query = count_query.where(and_(*conditions))

    # Total count
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Pagination
    offset = (page - 1) * limit
    query = query.order_by(Booking.created_at.desc()).offset(offset).limit(limit)

    result = await db.execute(query)
    bookings = result.scalars().all()

    return paginated_response(
        data=[booking_to_response(b) for b in bookings],
        page=page,
        limit=limit,
        total=total,
    )


# ── GET /bookings/{booking_id} ──────────────────────────────────────────────

@router.get(
    "/{booking_id}",
    response_model=BookingResponse,
    summary="Get booking details by ID",
)
async def get_booking_detail(
    booking_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns single booking detail.
    Enforces authorization:
    - Customer can only view their own bookings.
    - Worker can only view bookings assigned to them.
    - Admin can view any booking.
    """
    result = await db.execute(
        select(Booking).where(Booking.id == booking_id)
    )
    booking = result.scalar_one_or_none()

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Booking with id '{booking_id}' not found.",
        )

    # Ownership check
    if current_user.role == UserRole.CUSTOMER and booking.customer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You can only view your own bookings.",
        )
    elif current_user.role == UserRole.WORKER:
        worker_res = await db.execute(
            select(Worker.id).where(Worker.user_id == current_user.id)
        )
        worker_id = worker_res.scalar_one_or_none()
        if booking.worker_id != worker_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: You can only view bookings assigned to you.",
            )

    return booking_to_response(booking)


# ── PATCH /bookings/{booking_id}/status ─────────────────────────────────────

@router.patch(
    "/{booking_id}/status",
    response_model=BookingResponse,
    summary="Update booking status with state transition validation",
)
async def update_booking_status(
    booking_id: UUID,
    payload: BookingStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Updates the booking status:
    - Enforces valid state transitions per the booking status state machine:
      pending → assigned → accepted → en_route → in_progress → completed,
      plus rejected, cancelled, unassigned.
    - Rejects illegal transitions with a 400 Bad Request.
    - Appends an entry to the booking's timeline for tracking.
    - Updates worker availability and workload upon acceptance/completion.
    """
    result = await db.execute(
        select(Booking).where(Booking.id == booking_id)
    )
    booking = result.scalar_one_or_none()

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Booking with id '{booking_id}' not found.",
        )

    current_status = booking.status
    new_status = payload.status

    # Validate transition
    allowed_transitions = VALID_STATUS_TRANSITIONS.get(current_status, set())
    if new_status not in allowed_transitions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Invalid status transition from '{current_status.value}' to '{new_status.value}'. "
                f"Allowed transitions from '{current_status.value}': "
                f"{[s.value for s in allowed_transitions] if allowed_transitions else 'None (Terminal state)'}"
            ),
        )

    # Authorization checks per role
    if current_user.role == UserRole.CUSTOMER:
        if booking.customer_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: You can only update your own bookings.",
            )
        # Customer can only cancel
        if new_status != BookingStatus.CANCELLED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: Customers can only cancel bookings.",
            )

    elif current_user.role == UserRole.WORKER:
        worker_res = await db.execute(
            select(Worker).where(Worker.user_id == current_user.id)
        )
        worker = worker_res.scalar_one_or_none()
        if not worker or booking.worker_id != worker.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: You can only update bookings assigned to you.",
            )
        # Worker updates availability and workload
        if new_status == BookingStatus.ACCEPTED:
            worker.availability = WorkerAvailability.BUSY
            db.add(worker)
        elif new_status == BookingStatus.COMPLETED:
            worker.availability = WorkerAvailability.AVAILABLE
            worker.workload_this_week = (worker.workload_this_week or 0) + 1
            db.add(worker)
        elif new_status == BookingStatus.REJECTED:
            # Worker rejected; worker availability stays available
            worker.availability = WorkerAvailability.AVAILABLE
            db.add(worker)

    # Append to timeline
    now = datetime.now(timezone.utc)
    new_timeline_entry = {
        "status": new_status.value,
        "timestamp": now.isoformat(),
        "note": payload.note or f"Status changed to {new_status.value}",
    }
    booking.timeline = list(booking.timeline or []) + [new_timeline_entry]
    booking.status = new_status
    booking.updated_at = now

    db.add(booking)
    await db.commit()
    await db.refresh(booking)

    logger.info(
        f"[BOOKINGS] Booking {booking.id} transitioned from {current_status.value} to {new_status.value} "
        f"by user {current_user.id} ({current_user.role.value})"
    )

    return booking_to_response(booking)
