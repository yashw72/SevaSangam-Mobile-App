"""
Admin — Complaints Router.

Endpoints (all require role=admin):
  GET  /admin/complaints               — List with status tabs (open/in_review/resolved)
  GET  /admin/complaints/{id}          — Complaint detail (parties, booking link, description)
  POST /admin/complaints/{id}/start-review — Transition open → in_review
  POST /admin/complaints/{id}/add-note    — Add an admin note (stays in same status)
  POST /admin/complaints/{id}/resolve     — Transition in_review → resolved (note optional)
  POST /admin/complaints/{id}/reject      — Transition open|in_review → rejected (reason required)

Context (mobile context §10.6):
  "Complaints — list with status tabs (open/in_review/resolved), complaint detail
   (parties, booking link, description), actions: start review, add note, resolve, reject."

Valid transitions (mirroring the mobile state machine):
  open       → in_review | rejected
  in_review  → resolved  | rejected
  resolved   → (terminal)
  rejected   → (terminal)
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user, require_role
from app.db.session import get_db
from backend.app.models.user import User
from backend.app.models.complaint import Complaint
from backend.app.models.enums import ComplaintStatus

logger = logging.getLogger("sevasangam.admin.complaints")

router = APIRouter(
    prefix="/admin/complaints",
    tags=["Admin — Complaints"],
    dependencies=[Depends(require_role("admin"))],
)

# ── State machine ─────────────────────────────────────────────────────────────

VALID_COMPLAINT_TRANSITIONS: dict[ComplaintStatus, set[ComplaintStatus]] = {
    ComplaintStatus.OPEN:      {ComplaintStatus.IN_REVIEW, ComplaintStatus.REJECTED},
    ComplaintStatus.IN_REVIEW: {ComplaintStatus.RESOLVED,  ComplaintStatus.REJECTED},
    ComplaintStatus.RESOLVED:  set(),   # terminal
    ComplaintStatus.REJECTED:  set(),   # terminal
}


# ── Schemas ───────────────────────────────────────────────────────────────────

class NotePayload(BaseModel):
    note: str = Field(..., min_length=1, description="Admin note to attach.")


class ResolvePayload(BaseModel):
    note: Optional[str] = Field(None, description="Optional resolution summary.")


class RejectPayload(BaseModel):
    reason: str = Field(..., min_length=5, description="Rejection reason (required, shown to the filer).")


# ── Helpers ───────────────────────────────────────────────────────────────────

def paginated_response(data: list, page: int, limit: int, total: int) -> dict:
    return {
        "data": data,
        "page": page,
        "limit": limit,
        "total": total,
        "totalPages": max(1, (total + limit - 1) // limit),
    }


def complaint_to_dict(c: Complaint) -> dict:
    return {
        "id": str(c.id),
        "raisedBy": str(c.raised_by) if c.raised_by else None,
        "bookingId": str(c.booking_id) if c.booking_id else None,
        "workerId": str(c.worker_id) if c.worker_id else None,
        "category": c.category,
        "description": c.description,
        "status": c.status.value if c.status else None,
        "resolutionNote": c.resolution_note,
        "createdAt": c.created_at.isoformat() if c.created_at else None,
        "updatedAt": c.updated_at.isoformat() if c.updated_at else None,
    }


async def _get_complaint_or_404(complaint_id: UUID, db: AsyncSession) -> Complaint:
    result = await db.execute(select(Complaint).where(Complaint.id == complaint_id))
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Complaint '{complaint_id}' not found.",
        )
    return c


def _assert_transition(complaint: Complaint, target: ComplaintStatus) -> None:
    """Raises 400 if the target transition is not valid from the current status."""
    allowed = VALID_COMPLAINT_TRANSITIONS.get(complaint.status, set())
    if target not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Cannot transition complaint from '{complaint.status.value}' to '{target.value}'. "
                f"Allowed transitions: {[s.value for s in allowed] or 'none (terminal state)'}."
            ),
        )


async def _do_transition(
    complaint: Complaint,
    target: ComplaintStatus,
    note: Optional[str],
    db: AsyncSession,
) -> Complaint:
    now = datetime.now(timezone.utc)
    complaint.status = target
    complaint.resolution_note = note or complaint.resolution_note
    complaint.updated_at = now
    db.add(complaint)
    await db.commit()
    await db.refresh(complaint)
    return complaint


# ── GET /admin/complaints ─────────────────────────────────────────────────────

@router.get("", summary="List complaints (admin only)")
async def list_complaints_admin(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    complaint_status: Optional[ComplaintStatus] = Query(None, alias="status",
        description="Filter by status tab: open | in_review | resolved | rejected"),
    raised_by: Optional[UUID] = Query(None, alias="raisedBy"),
    worker_id: Optional[UUID] = Query(None, alias="workerId"),
    booking_id: Optional[UUID] = Query(None, alias="bookingId"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Supports the admin complaints list view with status tabs.
    Multiple filters can be combined.
    Ordered by created_at asc (oldest unresolved first — triage priority).
    """
    base_q = select(Complaint)
    count_q = select(func.count(Complaint.id))

    if complaint_status:
        base_q = base_q.where(Complaint.status == complaint_status)
        count_q = count_q.where(Complaint.status == complaint_status)
    if raised_by:
        base_q = base_q.where(Complaint.raised_by == raised_by)
        count_q = count_q.where(Complaint.raised_by == raised_by)
    if worker_id:
        base_q = base_q.where(Complaint.worker_id == worker_id)
        count_q = count_q.where(Complaint.worker_id == worker_id)
    if booking_id:
        base_q = base_q.where(Complaint.booking_id == booking_id)
        count_q = count_q.where(Complaint.booking_id == booking_id)

    total = (await db.execute(count_q)).scalar_one()
    offset = (page - 1) * limit
    result = await db.execute(
        base_q.order_by(Complaint.created_at.asc()).offset(offset).limit(limit)
    )
    complaints = result.scalars().all()

    return paginated_response(
        data=[complaint_to_dict(c) for c in complaints],
        page=page,
        limit=limit,
        total=total,
    )


# ── GET /admin/complaints/{id} ────────────────────────────────────────────────

@router.get("/{complaint_id}", summary="Complaint detail (admin only)")
async def get_complaint_detail(
    complaint_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    c = await _get_complaint_or_404(complaint_id, db)
    return complaint_to_dict(c)


# ── POST /admin/complaints/{id}/start-review ──────────────────────────────────

@router.post("/{complaint_id}/start-review", summary="Start reviewing an open complaint")
async def start_review(
    complaint_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Transitions open → in_review. Idempotent guard via state machine check."""
    c = await _get_complaint_or_404(complaint_id, db)
    _assert_transition(c, ComplaintStatus.IN_REVIEW)
    c = await _do_transition(c, ComplaintStatus.IN_REVIEW, note=None, db=db)
    logger.info(f"[ADMIN][COMPLAINTS] {complaint_id} → in_review by admin={current_user.id}")
    return {"message": "Complaint moved to in_review.", "complaint": complaint_to_dict(c)}


# ── POST /admin/complaints/{id}/add-note ──────────────────────────────────────

@router.post("/{complaint_id}/add-note", summary="Add an admin note without changing status")
async def add_note(
    complaint_id: UUID,
    payload: NotePayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Appends/replaces the resolution_note without moving the complaint to a new status.
    Useful for internal comments visible to the admin team.
    """
    c = await _get_complaint_or_404(complaint_id, db)
    if c.status in (ComplaintStatus.RESOLVED, ComplaintStatus.REJECTED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot add a note to a terminal complaint (status: '{c.status.value}').",
        )
    now = datetime.now(timezone.utc)
    c.resolution_note = payload.note
    c.updated_at = now
    db.add(c)
    await db.commit()
    await db.refresh(c)
    logger.info(f"[ADMIN][COMPLAINTS] Note added to {complaint_id} by admin={current_user.id}")
    return {"message": "Note added.", "complaint": complaint_to_dict(c)}


# ── POST /admin/complaints/{id}/resolve ───────────────────────────────────────

@router.post("/{complaint_id}/resolve", summary="Resolve a complaint under review")
async def resolve_complaint(
    complaint_id: UUID,
    payload: ResolvePayload = ResolvePayload(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Transitions in_review → resolved. Optional resolution note."""
    c = await _get_complaint_or_404(complaint_id, db)
    _assert_transition(c, ComplaintStatus.RESOLVED)
    c = await _do_transition(c, ComplaintStatus.RESOLVED, note=payload.note, db=db)
    logger.info(f"[ADMIN][COMPLAINTS] {complaint_id} → resolved by admin={current_user.id}")
    return {"message": "Complaint resolved.", "complaint": complaint_to_dict(c)}


# ── POST /admin/complaints/{id}/reject ────────────────────────────────────────

@router.post("/{complaint_id}/reject", summary="Reject a complaint (reason required)")
async def reject_complaint(
    complaint_id: UUID,
    payload: RejectPayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Transitions open|in_review → rejected. Reason is mandatory (422 if absent).
    The reason is stored in resolution_note.
    """
    c = await _get_complaint_or_404(complaint_id, db)
    _assert_transition(c, ComplaintStatus.REJECTED)
    c = await _do_transition(c, ComplaintStatus.REJECTED, note=payload.reason, db=db)
    logger.info(
        f"[ADMIN][COMPLAINTS] {complaint_id} → rejected by admin={current_user.id}. "
        f"Reason: {payload.reason!r}"
    )
    return {"message": "Complaint rejected.", "complaint": complaint_to_dict(c)}
