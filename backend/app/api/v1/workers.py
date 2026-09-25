"""
Workers Router for SevaSangam API.

Endpoints:
  GET    /workers                     — List workers with skill/distance/availability/cooperative/rating filters
  GET    /workers/me                  — Convenience endpoint for logged-in worker's own record
  GET    /workers/{worker_id}         — Get worker detail by ID
  PATCH  /workers/{worker_id}         — Self-update (availability, skills, service area, location)
  POST   /workers/{worker_id}/certificates — Upload certificate document (pending status, OCR stub)
  GET    /workers/{worker_id}/certificates — List certificates for a worker
"""

import logging
import os
import struct
import uuid
from datetime import datetime, timezone
from typing import Optional, List
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request,
    UploadFile,
    File,
    Form,
    status,
)
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from geoalchemy2.elements import WKTElement, WKBElement

from app.core.security import get_current_user
from app.db.session import get_db
from app.db.geo_queries import build_nearby_workers_query
from backend.app.models.user import User
from backend.app.models.worker import Worker
from backend.app.models.certificate import Certificate
from backend.app.models.enums import (
    UserRole,
    VerificationStatus,
    WorkerAvailability,
    CertificateStatus,
    InsuranceStatus,
)
from app.schemas.worker import (
    WorkerResponse,
    WorkerUpdate,
    LocationSchema,
    InsuranceSchema,
)
from app.schemas.certificate import (
    CertificateResponse,
    CertificateBase,
    OcrSchema,
)

logger = logging.getLogger("sevasangam.workers")

router = APIRouter(prefix="/workers", tags=["Workers"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads", "certificates")


# ── Location & Model Serialization Helpers ─────────────────────────────────

def parse_location(loc) -> Optional[LocationSchema]:
    """
    Safely decodes WKBElement, WKTElement, dict, or string into LocationSchema(lat, lng).
    Works without requiring shapely.
    """
    if loc is None:
        return None
    if isinstance(loc, LocationSchema):
        return loc
    if isinstance(loc, dict):
        return LocationSchema(**loc)
    if isinstance(loc, (str, WKTElement)):
        s = str(loc)
        if "POINT" in s.upper():
            coords = s.upper().split("POINT")[1].strip("() \t\n;").split()
            if len(coords) >= 2:
                # WKT is POINT(lng lat)
                return LocationSchema(lat=float(coords[1]), lng=float(coords[0]))
    if hasattr(loc, "data"):
        data = loc.data
        if isinstance(data, memoryview):
            data = data.tobytes()
        elif isinstance(data, str):
            data = bytes.fromhex(data)
        if isinstance(data, bytes) and len(data) >= 21:
            byte_order = "<" if data[0] == 1 else ">"
            geom_type = struct.unpack(f"{byte_order}I", data[1:5])[0]
            offset = 5
            if geom_type & 0x20000000:  # PostGIS EWKB with SRID
                offset += 4
            lng, lat = struct.unpack(f"{byte_order}dd", data[offset : offset + 16])
            return LocationSchema(lat=lat, lng=lng)
    return None


def worker_to_response(w: Worker) -> WorkerResponse:
    """
    Maps a SQLAlchemy Worker instance (with flattened columns) to the nested WorkerResponse schema.
    """
    now = datetime.now(timezone.utc)
    return WorkerResponse(
        id=w.id,
        user_id=w.user_id,
        cooperative_id=w.cooperative_id,
        skills=w.skills or [],
        experience_years=w.experience_years,
        rating=w.rating,
        rating_count=w.rating_count,
        verification_status=w.verification_status,
        availability=w.availability,
        location=parse_location(w.location),
        service_radius_km=w.service_radius_km,
        workload_this_week=w.workload_this_week,
        insurance=InsuranceSchema(
            status=w.insurance_status,
            coverage=w.insurance_coverage,
            valid_till=w.insurance_valid_till,
        ),
        created_at=w.created_at or now,
        updated_at=w.updated_at or now,
    )


def certificate_to_response(cert: Certificate) -> CertificateResponse:
    """
    Maps a SQLAlchemy Certificate instance to CertificateResponse schema.
    """
    now = datetime.now(timezone.utc)
    return CertificateResponse(
        id=cert.id or uuid.uuid4(),
        worker_id=cert.worker_id,
        type=cert.type,
        image_url=cert.image_url,
        ocr=OcrSchema(
            text=cert.ocr_text,
            confidence=cert.ocr_confidence,
        ),
        status=cert.status,
        review_note=cert.review_note,
        created_at=cert.created_at or now,
        updated_at=cert.updated_at or now,
    )


def paginated_response(data: list, page: int, limit: int, total: int) -> dict:
    """Standard paginated envelope per mobile contract."""
    return {
        "data": data,
        "page": page,
        "limit": limit,
        "total": total,
        "totalPages": max(1, (total + limit - 1) // limit),
    }


# ── GET /workers ────────────────────────────────────────────────────────────

@router.get(
    "",
    summary="List workers with skill/distance/availability/cooperative/rating filters",
)
async def list_workers(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    skill: Optional[str] = Query(None, description="Filter by skill (e.g. plumbing, electrician)"),
    lat: Optional[float] = Query(None, ge=-90, le=90, description="Customer latitude for distance calculation"),
    lng: Optional[float] = Query(None, ge=-180, le=180, description="Customer longitude for distance calculation"),
    radius_km: float = Query(10.0, ge=0.5, le=100.0, description="Search radius in kilometers (default 10km)"),
    availability: Optional[str] = Query(None, description="Worker availability: available, busy, offline"),
    cooperative_id: Optional[UUID] = Query(None, description="Filter by cooperative UUID"),
    min_rating: Optional[float] = Query(None, ge=0.0, le=5.0, description="Minimum worker rating"),
    verification_status: Optional[str] = Query(
        "verified",
        description="Verification status filter (default: verified). Use 'all' or specific status for admin.",
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns a paginated list of workers matching query criteria.
    - When `lat` and `lng` are provided, uses Lokesh's PostGIS spatial query (`build_nearby_workers_query`)
      sorted by distance.
    - When `lat` and `lng` are absent, falls back to rating and creation date ordering.
    """
    # Parse availability enum if provided
    avail_enum: Optional[WorkerAvailability] = None
    if availability:
        try:
            avail_enum = WorkerAvailability(availability.strip().lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid availability '{availability}'. Must be one of: available, busy, offline.",
            )

    # Parse verification status filter
    verif_enum: Optional[VerificationStatus] = None
    if verification_status and verification_status.strip().lower() != "all":
        try:
            verif_enum = VerificationStatus(verification_status.strip().lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid verification_status '{verification_status}'. Must be: pending, verified, rejected, suspended, or all.",
            )

    # Clean skill filter
    clean_skill = skill.strip().lower() if skill else None

    # Spatial query branch
    if lat is not None and lng is not None:
        # Use Lokesh's geo-query helper
        base_stmt = build_nearby_workers_query(
            lat=lat,
            lng=lng,
            radius_km=radius_km,
            skill=clean_skill,
            verification_status=verif_enum,
            availability=avail_enum,
        )

        # Apply cooperative and rating filters
        if cooperative_id is not None:
            base_stmt = base_stmt.where(Worker.cooperative_id == cooperative_id)
        if min_rating is not None:
            base_stmt = base_stmt.where(Worker.rating >= min_rating)

        # Count total
        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total_result = await db.execute(count_stmt)
        total = total_result.scalar_one()

        # Apply pagination
        offset = (page - 1) * limit
        paginated_stmt = base_stmt.offset(offset).limit(limit)

        result = await db.execute(paginated_stmt)
        rows = result.all()
        # Row format: (Worker, distance_km)
        workers = [row[0] for row in rows]

    else:
        # Non-spatial standard query branch
        query = select(Worker)
        count_query = select(func.count(Worker.id))

        conditions = []
        if verif_enum is not None:
            conditions.append(Worker.verification_status == verif_enum)
        if avail_enum is not None:
            conditions.append(Worker.availability == avail_enum)
        if clean_skill:
            conditions.append(Worker.skills.any(clean_skill))
        if cooperative_id is not None:
            conditions.append(Worker.cooperative_id == cooperative_id)
        if min_rating is not None:
            conditions.append(Worker.rating >= min_rating)

        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        total_result = await db.execute(count_query)
        total = total_result.scalar_one()

        offset = (page - 1) * limit
        query = query.order_by(Worker.rating.desc(), Worker.created_at.desc()).offset(offset).limit(limit)

        result = await db.execute(query)
        workers = result.scalars().all()

    worker_responses = [worker_to_response(w) for w in workers]

    logger.info(
        f"[WORKERS] Listed workers: page={page}, limit={limit}, total={total}, "
        f"geo={lat is not None and lng is not None}, skill={clean_skill}"
    )

    return paginated_response(
        data=worker_responses,
        page=page,
        limit=limit,
        total=total,
    )


# ── GET /workers/me ─────────────────────────────────────────────────────────

@router.get(
    "/me",
    response_model=WorkerResponse,
    summary="Get current authenticated worker's profile",
)
async def get_my_worker_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns the Worker record for the currently logged-in user.
    """
    result = await db.execute(
        select(Worker).where(Worker.user_id == current_user.id)
    )
    worker = result.scalar_one_or_none()

    if not worker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worker profile not found for the current user.",
        )

    return worker_to_response(worker)


# ── GET /workers/{worker_id} ────────────────────────────────────────────────

@router.get(
    "/{worker_id}",
    response_model=WorkerResponse,
    summary="Get worker profile by ID",
)
async def get_worker_detail(
    worker_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns the public worker profile by Worker UUID.
    """
    result = await db.execute(
        select(Worker).where(Worker.id == worker_id)
    )
    worker = result.scalar_one_or_none()

    if not worker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Worker with id '{worker_id}' not found.",
        )

    return worker_to_response(worker)


# ── PATCH /workers/{worker_id} ──────────────────────────────────────────────

@router.patch(
    "/{worker_id}",
    response_model=WorkerResponse,
    summary="Self-update worker profile (availability, skills, service area, location)",
)
async def update_worker_profile(
    worker_id: UUID,
    payload: WorkerUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Allows a worker to update their own record:
    - Toggle availability (available / busy / offline)
    - Update skills list
    - Update service radius (km)
    - Update location coordinates (lat, lng)
    - Update experience years
    
    Enforces that workers can only PATCH their own profile (Admins can also edit).
    Workers cannot self-approve verification_status.
    """
    result = await db.execute(
        select(Worker).where(Worker.id == worker_id)
    )
    worker = result.scalar_one_or_none()

    if not worker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Worker with id '{worker_id}' not found.",
        )

    # Enforce ownership: only the worker themselves or an admin can PATCH
    if current_user.role != UserRole.ADMIN and worker.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You can only update your own worker profile.",
        )

    # Disallow self-verification for non-admins
    if current_user.role != UserRole.ADMIN and payload.verification_status is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Workers cannot modify their own verification status.",
        )

    # Apply availability
    if payload.availability is not None:
        worker.availability = payload.availability

    # Apply skills
    if payload.skills is not None:
        worker.skills = [s.strip().lower() for s in payload.skills if s.strip()]

    # Apply experience years
    if payload.experience_years is not None:
        worker.experience_years = payload.experience_years

    # Apply service radius
    if payload.service_radius_km is not None:
        worker.service_radius_km = payload.service_radius_km

    # Apply location update if provided
    if payload.location is not None:
        point_wkt = f"POINT({payload.location.lng} {payload.location.lat})"
        worker.location = WKTElement(point_wkt, srid=4326)

    # Apply cooperative affiliation
    if payload.cooperative_id is not None:
        worker.cooperative_id = payload.cooperative_id

    # Apply insurance if provided
    if payload.insurance is not None:
        worker.insurance_status = payload.insurance.status
        if payload.insurance.coverage is not None:
            worker.insurance_coverage = payload.insurance.coverage
        if payload.insurance.valid_till is not None:
            worker.insurance_valid_till = payload.insurance.valid_till

    # Admin only verification status
    if current_user.role == UserRole.ADMIN and payload.verification_status is not None:
        worker.verification_status = payload.verification_status

    db.add(worker)
    await db.commit()
    await db.refresh(worker)

    logger.info(f"[WORKERS] Worker {worker.id} updated by user {current_user.id}")

    return worker_to_response(worker)


# ── POST /workers/{worker_id}/certificates ──────────────────────────────────

@router.post(
    "/{worker_id}/certificates",
    response_model=CertificateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload certificate for worker verification",
)
async def upload_certificate(
    worker_id: UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Accepts certificate document image / reference for verification.
    Supports either:
    - JSON payload: { "type": "license_name", "imageUrl": "https://..." }
    - Multipart form: type="...", file=<binary image> or imageUrl="..."

    Marks certificate status as 'pending'.
    Actual OCR processing is wired in Yash-Thakur's task; stubbed with TODO.
    Enforces that workers can only upload certificates for their own profile.
    """
    result = await db.execute(
        select(Worker).where(Worker.id == worker_id)
    )
    worker = result.scalar_one_or_none()

    if not worker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Worker with id '{worker_id}' not found.",
        )

    # Enforce ownership: only the worker themselves or an admin can upload
    if current_user.role != UserRole.ADMIN and worker.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You can only upload certificates to your own profile.",
        )

    # Determine content-type (JSON vs multipart form)
    content_type = request.headers.get("content-type", "")
    cert_type: Optional[str] = None
    image_url: Optional[str] = None

    if "application/json" in content_type:
        try:
            body = await request.json()
            cert_type = body.get("type")
            image_url = body.get("imageUrl") or body.get("image_url")
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON payload.",
            )
    else:
        # Multipart / form-data
        try:
            form = await request.form()
            cert_type = form.get("type")
            image_url = form.get("imageUrl") or form.get("image_url")
            upload_file = form.get("file")

            if upload_file and hasattr(upload_file, "filename") and upload_file.filename:
                # Save file to disk
                os.makedirs(UPLOAD_DIR, exist_ok=True)
                ext = os.path.splitext(upload_file.filename)[1] or ".jpg"
                saved_filename = f"{worker_id}_{uuid.uuid4().hex[:8]}{ext}"
                file_path = os.path.join(UPLOAD_DIR, saved_filename)
                
                content = await upload_file.read()
                with open(file_path, "wb") as f:
                    f.write(content)
                image_url = f"/uploads/certificates/{saved_filename}"
        except Exception as e:
            logger.warning(f"[WORKERS] Form parsing error: {e}")

    if not cert_type or not cert_type.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Certificate 'type' is required (e.g. 'electrician_license', 'plumbing_cert').",
        )

    # Create certificate in PENDING status
    cert = Certificate(
        worker_id=worker.id,
        type=cert_type.strip(),
        image_url=image_url,
        status=CertificateStatus.PENDING,
        review_note=None,
        # TODO (Yash-Thakur): Wire in OpenCV deskew/threshold + Tesseract OCR via backend.app.ai.ocr
        # Example target:
        #   ocr_result = await extract_certificate_ocr(file_path or image_url)
        #   cert.ocr_text = ocr_result.get("text")
        #   cert.ocr_confidence = ocr_result.get("confidence")
        ocr_text=None,
        ocr_confidence=None,
    )

    db.add(cert)
    await db.commit()
    await db.refresh(cert)

    logger.info(
        f"[WORKERS] Certificate {cert.id} ({cert.type}) uploaded for worker {worker.id}. "
        f"Status: {cert.status}"
    )

    return certificate_to_response(cert)


# ── GET /workers/{worker_id}/certificates ───────────────────────────────────

@router.get(
    "/{worker_id}/certificates",
    response_model=List[CertificateResponse],
    summary="List certificates for a worker",
)
async def list_worker_certificates(
    worker_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns all uploaded certificates for the specified worker.
    """
    # Verify worker exists
    worker_result = await db.execute(
        select(Worker).where(Worker.id == worker_id)
    )
    if not worker_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Worker with id '{worker_id}' not found.",
        )

    result = await db.execute(
        select(Certificate)
        .where(Certificate.worker_id == worker_id)
        .order_by(Certificate.created_at.desc())
    )
    certificates = result.scalars().all()

    return [certificate_to_response(c) for c in certificates]
