"""
Admin — Welfare Programmes Router.

Endpoints (all require role=admin):
  GET    /admin/welfare              — List programmes (filter by type/status)
  POST   /admin/welfare              — Create a new programme
  GET    /admin/welfare/{id}         — Programme detail
  PATCH  /admin/welfare/{id}         — Edit programme (title, description, eligibility, status)
  DELETE /admin/welfare/{id}         — Delete a programme (only draft; active/closed are protected)
  POST   /admin/welfare/{id}/announce — Stub: announce to workers (triggers a mock notification)

Context (mobile context §10.8):
  "Welfare programmes — list of programmes (insurance, health, training…), enrolment counts,
   worker insurance coverage overview; create/edit programme (title, description, eligibility,
   status) and announce to workers (mock)."

Announce is a stub that logs the announcement and returns a confirmation;
real push notification integration is wired in the Notifications prompt.
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
from backend.app.models.welfare_program import WelfareProgram
from backend.app.models.enums import WelfareProgramType, WelfareProgramStatus

logger = logging.getLogger("sevasangam.admin.welfare")

router = APIRouter(
    prefix="/admin/welfare",
    tags=["Admin — Welfare Programmes"],
    dependencies=[Depends(require_role("admin"))],
)


# ── Schemas ───────────────────────────────────────────────────────────────────

class WelfareProgramCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    type: WelfareProgramType
    eligibility: Optional[str] = Field(None, max_length=500)
    status: WelfareProgramStatus = WelfareProgramStatus.DRAFT


class WelfareProgramUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    eligibility: Optional[str] = Field(None, max_length=500)
    status: Optional[WelfareProgramStatus] = None


class AnnouncePayload(BaseModel):
    message: Optional[str] = Field(
        None,
        description="Custom announcement message. Defaults to programme title if omitted.",
    )


# ── Helpers ───────────────────────────────────────────────────────────────────

def paginated_response(data: list, page: int, limit: int, total: int) -> dict:
    return {
        "data": data,
        "page": page,
        "limit": limit,
        "total": total,
        "totalPages": max(1, (total + limit - 1) // limit),
    }


def program_to_dict(p: WelfareProgram) -> dict:
    return {
        "id": str(p.id),
        "title": p.title,
        "description": p.description,
        "type": p.type.value if p.type else None,
        "eligibility": p.eligibility,
        "enrolledCount": p.enrolled_count,
        "status": p.status.value if p.status else None,
        "createdAt": p.created_at.isoformat() if p.created_at else None,
        "updatedAt": p.updated_at.isoformat() if p.updated_at else None,
    }


async def _get_program_or_404(program_id: UUID, db: AsyncSession) -> WelfareProgram:
    result = await db.execute(select(WelfareProgram).where(WelfareProgram.id == program_id))
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Welfare programme '{program_id}' not found.",
        )
    return p


# ── GET /admin/welfare ────────────────────────────────────────────────────────

@router.get("", summary="List welfare programmes (admin only)")
async def list_welfare_programs(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    program_type: Optional[WelfareProgramType] = Query(None, alias="type"),
    program_status: Optional[WelfareProgramStatus] = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns all welfare programmes, filterable by type and status."""
    base_q = select(WelfareProgram)
    count_q = select(func.count(WelfareProgram.id))

    if program_type:
        base_q = base_q.where(WelfareProgram.type == program_type)
        count_q = count_q.where(WelfareProgram.type == program_type)
    if program_status:
        base_q = base_q.where(WelfareProgram.status == program_status)
        count_q = count_q.where(WelfareProgram.status == program_status)

    total = (await db.execute(count_q)).scalar_one()
    offset = (page - 1) * limit
    result = await db.execute(
        base_q.order_by(WelfareProgram.created_at.desc()).offset(offset).limit(limit)
    )
    programs = result.scalars().all()

    return paginated_response(
        data=[program_to_dict(p) for p in programs],
        page=page,
        limit=limit,
        total=total,
    )


# ── POST /admin/welfare ───────────────────────────────────────────────────────

@router.post("", status_code=status.HTTP_201_CREATED, summary="Create a welfare programme")
async def create_welfare_program(
    payload: WelfareProgramCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    program = WelfareProgram(
        id=uuid.uuid4(),
        title=payload.title,
        description=payload.description,
        type=payload.type,
        eligibility=payload.eligibility,
        enrolled_count=0,
        status=payload.status,
        created_at=now,
        updated_at=now,
    )
    db.add(program)
    await db.commit()
    await db.refresh(program)

    logger.info(
        f"[ADMIN][WELFARE] Programme '{program.title}' ({program.id}) created by admin={current_user.id}"
    )
    return program_to_dict(program)


# ── GET /admin/welfare/{id} ───────────────────────────────────────────────────

@router.get("/{program_id}", summary="Welfare programme detail")
async def get_welfare_program(
    program_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    p = await _get_program_or_404(program_id, db)
    return program_to_dict(p)


# ── PATCH /admin/welfare/{id} ─────────────────────────────────────────────────

@router.patch("/{program_id}", summary="Edit a welfare programme")
async def update_welfare_program(
    program_id: UUID,
    payload: WelfareProgramUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Partial update: only provided fields are modified.
    Closed programmes cannot be re-activated (status changes from closed → active/draft are blocked).
    """
    p = await _get_program_or_404(program_id, db)

    if p.status == WelfareProgramStatus.CLOSED and payload.status and payload.status != WelfareProgramStatus.CLOSED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Closed welfare programmes cannot be re-opened. Create a new programme instead.",
        )

    now = datetime.now(timezone.utc)
    if payload.title is not None:
        p.title = payload.title
    if payload.description is not None:
        p.description = payload.description
    if payload.eligibility is not None:
        p.eligibility = payload.eligibility
    if payload.status is not None:
        p.status = payload.status
    p.updated_at = now

    db.add(p)
    await db.commit()
    await db.refresh(p)

    logger.info(f"[ADMIN][WELFARE] Programme {program_id} updated by admin={current_user.id}")
    return program_to_dict(p)


# ── DELETE /admin/welfare/{id} ────────────────────────────────────────────────

@router.delete("/{program_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Delete a welfare programme (draft only)")
async def delete_welfare_program(
    program_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Hard-deletes a programme. Only DRAFT programmes can be deleted — active and
    closed programmes are protected (they may have enrolled workers and an audit trail).
    """
    p = await _get_program_or_404(program_id, db)

    if p.status != WelfareProgramStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Only draft programmes can be deleted. "
                f"This programme is '{p.status.value}'. "
                f"Set status to 'closed' instead."
            ),
        )

    await db.delete(p)
    await db.commit()
    logger.info(f"[ADMIN][WELFARE] Programme {program_id} deleted by admin={current_user.id}")
    # 204 — no body


# ── POST /admin/welfare/{id}/announce ────────────────────────────────────────

@router.post("/{program_id}/announce", summary="Announce a welfare programme to all workers (stub)")
async def announce_welfare_program(
    program_id: UUID,
    payload: AnnouncePayload = AnnouncePayload(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Stub notification trigger — logs the announcement and returns a confirmation.
    Real FCM push notification wiring happens in the Notifications prompt.

    Only ACTIVE programmes can be announced (announcing a draft or closed programme
    would be confusing for workers).
    """
    p = await _get_program_or_404(program_id, db)

    if p.status != WelfareProgramStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Only active programmes can be announced. "
                f"This programme is '{p.status.value}'."
            ),
        )

    announcement_text = payload.message or (
        f"New welfare programme available: {p.title}. "
        f"Check the app for details and eligibility."
    )

    # TODO (Notifications prompt): replace this log with a real FCM broadcast
    # to all verified workers via the notifications service.
    logger.info(
        f"[ADMIN][WELFARE][STUB] Announcing programme {program_id} "
        f"('{p.title}') to all workers. Message: {announcement_text!r}. "
        f"Triggered by admin={current_user.id}"
    )

    return {
        "message": "Announcement queued (stub).",
        "programme": program_to_dict(p),
        "announcementText": announcement_text,
        "notificationStatus": "stub_logged",  # will become "sent" once FCM is wired
    }
