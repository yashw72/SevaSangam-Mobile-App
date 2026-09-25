"""
Reviews Router for SevaSangam API.

Endpoints:
  POST /reviews                      — Submit a review (completed bookings only, one per booking, customer-owned)
  GET  /workers/{worker_id}/reviews  — Paginated list of reviews for a specific worker

Rating aggregation:
  After each new review, the worker's `rating` and `rating_count` are updated
  using a simple running-average formula (no separate aggregate table needed for MVP):

    new_rating = ((old_rating * old_count) + new_stars) / (old_count + 1)
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from backend.app.models.user import User
from backend.app.models.worker import Worker
from backend.app.models.booking import Booking
from backend.app.models.review import Review
from backend.app.models.enums import UserRole, BookingStatus
from app.schemas.review import ReviewCreate, ReviewResponse

logger = logging.getLogger("sevasangam.reviews")

router = APIRouter(tags=["Reviews"])


# ── Helpers ──────────────────────────────────────────────────────────────────

def paginated_response(data: list, page: int, limit: int, total: int) -> dict:
    """Standard paginated envelope per mobile contract."""
    return {
        "data": data,
        "page": page,
        "limit": limit,
        "total": total,
        "totalPages": max(1, (total + limit - 1) // limit),
    }


def review_to_response(r: Review) -> ReviewResponse:
    now = datetime.now(timezone.utc)
    return ReviewResponse(
        id=r.id or uuid.uuid4(),
        booking_id=r.booking_id,
        customer_id=r.customer_id,
        worker_id=r.worker_id,
        stars=r.stars,
        comment=r.comment,
        tags=r.tags or [],
        created_at=r.created_at or now,
        updated_at=r.updated_at or now,
    )


# ── POST /reviews ─────────────────────────────────────────────────────────────

@router.post(
    "/reviews",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a review for a completed booking",
)
async def create_review(
    payload: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Rules enforced:
    1. Only authenticated customers can submit reviews (not workers, not admins).
    2. The booking must be in COMPLETED status.
    3. The requesting customer must own the booking (customerId matches).
    4. Only one review per booking (enforced at DB level by UNIQUE constraint on
       booking_id, and checked here in advance to return a clean 409 error).
    5. The worker's `rating` and `rating_count` are updated using a running average.
    """
    # Only customers can submit reviews
    if current_user.role != UserRole.CUSTOMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only customers can submit reviews.",
        )

    # Fetch and validate the booking
    booking_result = await db.execute(
        select(Booking).where(Booking.id == payload.booking_id)
    )
    booking = booking_result.scalar_one_or_none()

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Booking '{payload.booking_id}' not found.",
        )

    # Booking must be COMPLETED
    if booking.status != BookingStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Reviews can only be submitted for completed bookings. "
                f"This booking is currently '{booking.status.value}'."
            ),
        )

    # Customer must own the booking
    if booking.customer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You can only review bookings you own.",
        )

    # Confirm the worker exists and matches the booking's assigned worker
    worker_result = await db.execute(
        select(Worker).where(Worker.id == payload.worker_id)
    )
    worker = worker_result.scalar_one_or_none()

    if not worker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Worker '{payload.worker_id}' not found.",
        )

    if booking.worker_id != worker.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The workerId must match the worker assigned to this booking.",
        )

    # Check one-review-per-booking: pre-check for a clean 409 (DB UNIQUE is the backstop)
    existing_result = await db.execute(
        select(Review).where(Review.booking_id == payload.booking_id)
    )
    if existing_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A review for this booking already exists. Only one review per booking is allowed.",
        )

    now = datetime.now(timezone.utc)

    review = Review(
        id=uuid.uuid4(),
        booking_id=payload.booking_id,
        customer_id=current_user.id,  # always use the authenticated user, not payload
        worker_id=payload.worker_id,
        stars=payload.stars,
        comment=payload.comment,
        tags=payload.tags or [],
        created_at=now,
        updated_at=now,
    )

    # ── Running-average rating update ────────────────────────────────────────
    # new_rating = ((old_rating * old_count) + new_stars) / (old_count + 1)
    old_count = worker.rating_count or 0
    old_rating = worker.rating or 0.0
    new_count = old_count + 1
    new_rating = round(((old_rating * old_count) + payload.stars) / new_count, 2)

    worker.rating = new_rating
    worker.rating_count = new_count

    db.add(review)
    db.add(worker)

    try:
        await db.commit()
    except IntegrityError:
        # Race condition: another review was submitted concurrently for the same booking
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A review for this booking already exists (concurrent submission detected).",
        )

    await db.refresh(review)
    await db.refresh(worker)

    logger.info(
        f"[REVIEWS] Review {review.id} created for booking {review.booking_id}. "
        f"Worker {worker.id} rating: {old_rating:.2f}->{new_rating:.2f} "
        f"(count: {old_count}->{new_count})"
    )

    return review_to_response(review)


# ── GET /workers/{worker_id}/reviews ─────────────────────────────────────────

@router.get(
    "/workers/{worker_id}/reviews",
    summary="List reviews for a worker (paginated)",
)
async def list_worker_reviews(
    worker_id: UUID,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns a paginated list of reviews for the given worker.
    Available to all authenticated users (public worker profile data).
    Ordered by most recent first.
    """
    # Confirm worker exists
    worker_result = await db.execute(
        select(Worker).where(Worker.id == worker_id)
    )
    if not worker_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Worker '{worker_id}' not found.",
        )

    # Count total reviews
    count_result = await db.execute(
        select(func.count(Review.id)).where(Review.worker_id == worker_id)
    )
    total = count_result.scalar_one()

    # Fetch paginated reviews
    offset = (page - 1) * limit
    reviews_result = await db.execute(
        select(Review)
        .where(Review.worker_id == worker_id)
        .order_by(Review.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    reviews = reviews_result.scalars().all()

    return paginated_response(
        data=[review_to_response(r) for r in reviews],
        page=page,
        limit=limit,
        total=total,
    )
