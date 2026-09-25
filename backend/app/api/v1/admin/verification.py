"""
Admin — Verification Queue Router.

Endpoints (all require role=admin):
  GET  /admin/verification              — Pending certificate queue
  POST /admin/verification/{cert_id}/approve         — Approve a certificate
  POST /admin/verification/{cert_id}/reject          — Reject with required reason
  POST /admin/verification/{cert_id}/request-reupload — Ask worker to re-upload

Context (mobile context §10.2):
  "verification detail": profile, skills, cooperative membership, CertificateViewer
  (OCR result text/confidence, mocked). Actions: Approve / Reject (reason required)
  / Request re-upload.

On approve / reject the **worker's verification_status** is updated:
  - All certificates approved → worker becomes "verified"
  - Any certificate rejected  → worker becomes "rejected"
  - request-reupload          → worker stays "pending" (back to re-upload flow)

Reject calls the mobile WorkerAccountStatus screen path (status + reason displayed
to the worker). The reason field is mandatory for reject — returns 422 if absent.
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
from backend.app.models.worker import Worker
from backend.app.models.certificate import Certificate
from backend.app.models.enums import (
    CertificateStatus,
    VerificationStatus,
    UserRole,
)

logger = logging.getLogger("sevasangam.admin.verification")

router = APIRouter(
    prefix="/admin/verification",
    tags=["Admin — Verification"],
    dependencies=[Depends(require_role("admin"))],
)


# ── Schemas ──────────────────────────────────────────────────────────────────

class ApprovePayload(BaseModel):
    """Optional admin note on approval."""
    note: Optional[str] = None


class RejectPayload(BaseModel):
    """Reason is mandatory for rejection (surfaced in WorkerAccountStatus screen)."""
    reason: str = Field(..., min_length=5, description="Human-readable reason shown to the worker.")


class ReuploadPayload(BaseModel):
    """Admin note explaining what the worker should fix before re-uploading."""
    note: Optional[str] = Field(None, description="Instructions shown to the worker.")


# ── Helpers ──────────────────────────────────────────────────────────────────

def paginated_response(data: list, page: int, limit: int, total: int) -> dict:
    return {
        "data": data,
        "page": page,
        "limit": limit,
        "total": total,
        "totalPages": max(1, (total + limit - 1) // limit),
    }


def cert_to_dict(c: Certificate, worker: Optional[Worker] = None) -> dict:
    d = {
        "id": str(c.id),
        "workerId": str(c.worker_id),
        "type": c.type,
        "imageUrl": c.image_url,
        "status": c.status.value if c.status else None,
        "reviewNote": c.review_note,
        "ocr": {
            "text": c.ocr_text,
            "confidence": c.ocr_confidence,
        },
        "createdAt": c.created_at.isoformat() if c.created_at else None,
        "updatedAt": c.updated_at.isoformat() if c.updated_at else None,
    }
    if worker:
        d["worker"] = {
            "id": str(worker.id),
            "skills": worker.skills or [],
            "experienceYears": worker.experience_years,
            "verificationStatus": worker.verification_status.value if worker.verification_status else None,
            "rating": worker.rating,
            "ratingCount": worker.rating_count,
        }
    return d


async def _get_cert_or_404(cert_id: UUID, db: AsyncSession) -> Certificate:
    result = await db.execute(select(Certificate).where(Certificate.id == cert_id))
    cert = result.scalar_one_or_none()
    if not cert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificate '{cert_id}' not found.",
        )
    return cert


async def _get_worker_or_404(worker_id: UUID, db: AsyncSession) -> Worker:
    result = await db.execute(select(Worker).where(Worker.id == worker_id))
    worker = result.scalar_one_or_none()
    if not worker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Worker '{worker_id}' not found.",
        )
    return worker


async def _refresh_worker_verification_status(worker: Worker, db: AsyncSession) -> None:
    """
    Recalculate and persist a worker's overall verification_status based on
    the current state of ALL their certificates.

    Logic:
      - Any PENDING         → keep worker as PENDING   (review is in-progress)
      - All APPROVED        → set worker as VERIFIED
      - Any REJECTED        → set worker as REJECTED  (worker needs to fix & re-upload)
    Worker status SUSPENDED is set explicitly by the suspend action; we don't
    touch it from here.
    """
    if worker.verification_status == VerificationStatus.SUSPENDED:
        return  # leave suspended workers alone

    certs_result = await db.execute(
        select(Certificate).where(Certificate.worker_id == worker.id)
    )
    certs = certs_result.scalars().all()

    if not certs:
        return  # no certs uploaded yet — stay pending

    statuses = {c.status for c in certs}

    if CertificateStatus.PENDING in statuses:
        worker.verification_status = VerificationStatus.PENDING
    elif CertificateStatus.REJECTED in statuses:
        worker.verification_status = VerificationStatus.REJECTED
    else:
        # All approved
        worker.verification_status = VerificationStatus.VERIFIED

    worker.updated_at = datetime.now(timezone.utc)
    db.add(worker)


# ── GET /admin/verification — Pending certificate queue ──────────────────────

@router.get(
    "",
    summary="List pending certificates awaiting admin review",
)
async def list_pending_certificates(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    worker_id: Optional[UUID] = Query(None, alias="workerId", description="Filter by worker"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns certificates with status=pending, newest first.
    Optionally filter by workerId (for the verification detail screen).
    Includes inline worker summary for the mobile card view.
    """
    base_q = select(Certificate).where(Certificate.status == CertificateStatus.PENDING)
    count_q = select(func.count(Certificate.id)).where(Certificate.status == CertificateStatus.PENDING)

    if worker_id:
        base_q = base_q.where(Certificate.worker_id == worker_id)
        count_q = count_q.where(Certificate.worker_id == worker_id)

    total = (await db.execute(count_q)).scalar_one()

    offset = (page - 1) * limit
    certs_result = await db.execute(
        base_q.order_by(Certificate.created_at.asc()).offset(offset).limit(limit)
    )
    certs = certs_result.scalars().all()

    # Fetch workers for inline summary (batch)
    worker_ids = list({c.worker_id for c in certs})
    workers_map: dict[UUID, Worker] = {}
    if worker_ids:
        workers_result = await db.execute(
            select(Worker).where(Worker.id.in_(worker_ids))
        )
        workers_map = {w.id: w for w in workers_result.scalars().all()}

    return paginated_response(
        data=[cert_to_dict(c, workers_map.get(c.worker_id)) for c in certs],
        page=page,
        limit=limit,
        total=total,
    )


# ── POST /admin/verification/{cert_id}/approve ───────────────────────────────

@router.post(
    "/{cert_id}/approve",
    summary="Approve a pending certificate",
)
async def approve_certificate(
    cert_id: UUID,
    payload: ApprovePayload = ApprovePayload(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Marks the certificate as APPROVED (+ optional review note).
    Then recalculates the worker's overall verification_status:
      - If all certs approved → worker becomes VERIFIED.
      - If others still pending → worker stays PENDING.
    """
    cert = await _get_cert_or_404(cert_id, db)

    if cert.status == CertificateStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Certificate is already approved.",
        )

    now = datetime.now(timezone.utc)
    cert.status = CertificateStatus.APPROVED
    cert.review_note = payload.note
    cert.updated_at = now
    db.add(cert)

    # Recalculate worker's top-level verification_status
    worker = await _get_worker_or_404(cert.worker_id, db)
    await _refresh_worker_verification_status(worker, db)

    await db.commit()
    await db.refresh(cert)
    await db.refresh(worker)

    logger.info(
        f"[ADMIN][VERIFICATION] cert={cert_id} APPROVED by admin={current_user.id}. "
        f"Worker {worker.id} → verification_status={worker.verification_status.value}"
    )

    return {
        "message": "Certificate approved.",
        "certificate": cert_to_dict(cert, worker),
        "workerVerificationStatus": worker.verification_status.value,
    }


# ── POST /admin/verification/{cert_id}/reject ─────────────────────────────────

@router.post(
    "/{cert_id}/reject",
    summary="Reject a certificate with a mandatory reason",
)
async def reject_certificate(
    cert_id: UUID,
    payload: RejectPayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Marks the certificate as REJECTED. `reason` is mandatory (422 if absent)
    and is stored in `review_note`; the mobile WorkerAccountStatus screen
    surfaces it to the worker.

    Worker's verification_status is recalculated — will become REJECTED since
    at least one cert is now rejected.
    """
    cert = await _get_cert_or_404(cert_id, db)

    if cert.status == CertificateStatus.REJECTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Certificate is already rejected.",
        )

    now = datetime.now(timezone.utc)
    cert.status = CertificateStatus.REJECTED
    cert.review_note = payload.reason  # surfaces in the WorkerAccountStatus screen
    cert.updated_at = now
    db.add(cert)

    worker = await _get_worker_or_404(cert.worker_id, db)
    await _refresh_worker_verification_status(worker, db)

    await db.commit()
    await db.refresh(cert)
    await db.refresh(worker)

    logger.info(
        f"[ADMIN][VERIFICATION] cert={cert_id} REJECTED by admin={current_user.id}. "
        f"Reason: {payload.reason!r}. Worker {worker.id} → {worker.verification_status.value}"
    )

    return {
        "message": "Certificate rejected.",
        "certificate": cert_to_dict(cert, worker),
        "workerVerificationStatus": worker.verification_status.value,
    }


# ── POST /admin/verification/{cert_id}/request-reupload ──────────────────────

@router.post(
    "/{cert_id}/request-reupload",
    summary="Ask the worker to re-upload a certificate",
)
async def request_reupload(
    cert_id: UUID,
    payload: ReuploadPayload = ReuploadPayload(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Resets the certificate status back to PENDING (allowing the worker to upload
    a new image) and stores an optional admin note explaining what to fix.
    Worker's verification_status stays PENDING (no change needed — pending is correct).
    """
    cert = await _get_cert_or_404(cert_id, db)

    now = datetime.now(timezone.utc)
    cert.status = CertificateStatus.PENDING
    cert.review_note = payload.note
    cert.updated_at = now
    db.add(cert)

    # Always move worker back to PENDING (enables the re-upload flow in WorkerAccountStatus)
    # Exception: leave SUSPENDED workers alone — only the suspend/reactivate actions manage that.
    worker = await _get_worker_or_404(cert.worker_id, db)
    if worker.verification_status != VerificationStatus.SUSPENDED:
        worker.verification_status = VerificationStatus.PENDING
        worker.updated_at = now
        db.add(worker)

    await db.commit()
    await db.refresh(cert)

    logger.info(
        f"[ADMIN][VERIFICATION] cert={cert_id} → request-reupload by admin={current_user.id}. "
        f"Note: {payload.note!r}"
    )

    return {
        "message": "Re-upload requested. Worker has been notified.",
        "certificate": cert_to_dict(cert, worker),
    }
