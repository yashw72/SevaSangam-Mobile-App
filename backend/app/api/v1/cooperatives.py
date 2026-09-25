"""
Cooperatives Router for SevaSangam API.

Endpoints:
  GET  /cooperatives          — Paginated list with filters (any authenticated user)
  GET  /cooperatives/{id}     — Single cooperative detail
"""

import logging
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from backend.app.models.user import User
from backend.app.models.cooperative import Cooperative
from app.schemas.cooperative import CooperativeResponse

logger = logging.getLogger("sevasangam.cooperatives")

router = APIRouter(prefix="/cooperatives", tags=["Cooperatives"])


# ── Paginated response helper ──────────────────────────────────────────────

def paginated_response(data: list, page: int, limit: int, total: int) -> dict:
    """Build a standard paginated response envelope."""
    return {
        "data": data,
        "page": page,
        "limit": limit,
        "total": total,
        "totalPages": max(1, (total + limit - 1) // limit),
    }


# ── GET /cooperatives ──────────────────────────────────────────────────────

@router.get(
    "",
    summary="List cooperatives (paginated)",
)
async def list_cooperatives(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    region: Optional[str] = Query(None, description="Filter by region (exact match)"),
    verified: Optional[bool] = Query(None, description="Filter by verified status"),
    search: Optional[str] = Query(None, description="Search by cooperative name (partial match)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns a paginated list of cooperatives.
    Any authenticated user can access this — cooperatives are public directory info.
    Supports region, verified, and name search filters.
    """
    query = select(Cooperative)
    count_query = select(func.count(Cooperative.id))

    # Apply region filter
    if region:
        query = query.where(Cooperative.region == region.strip())
        count_query = count_query.where(Cooperative.region == region.strip())

    # Apply verified filter
    if verified is not None:
        query = query.where(Cooperative.verified == verified)
        count_query = count_query.where(Cooperative.verified == verified)

    # Apply search filter (name partial match)
    if search:
        search_pattern = f"%{search.strip()}%"
        query = query.where(Cooperative.name.ilike(search_pattern))
        count_query = count_query.where(Cooperative.name.ilike(search_pattern))

    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Apply pagination
    offset = (page - 1) * limit
    query = query.order_by(Cooperative.name.asc()).offset(offset).limit(limit)

    result = await db.execute(query)
    cooperatives = result.scalars().all()

    coop_responses = [CooperativeResponse.model_validate(c) for c in cooperatives]

    return paginated_response(
        data=coop_responses,
        page=page,
        limit=limit,
        total=total,
    )


# ── GET /cooperatives/{id} ─────────────────────────────────────────────────

@router.get(
    "/{cooperative_id}",
    response_model=CooperativeResponse,
    summary="Get cooperative details",
)
async def get_cooperative(
    cooperative_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns details for a single cooperative by ID.
    """
    result = await db.execute(
        select(Cooperative).where(Cooperative.id == cooperative_id)
    )
    cooperative = result.scalar_one_or_none()

    if not cooperative:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cooperative with id '{cooperative_id}' not found.",
        )

    return CooperativeResponse.model_validate(cooperative)
