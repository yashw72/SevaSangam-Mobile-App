"""
Service Categories Router for SevaSangam API.

Endpoints:
  GET /service_categories — List all available service categories
  GET /service_categories/{category_id} — Get details for a specific service category
"""

import logging
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from backend.app.models.user import User
from backend.app.models.service_category import ServiceCategory
from app.schemas.service_category import ServiceCategoryResponse

logger = logging.getLogger("sevasangam.service_categories")

router = APIRouter(prefix="/service_categories", tags=["Service Categories"])


@router.get(
    "",
    response_model=List[ServiceCategoryResponse],
    summary="List all service categories",
)
async def list_service_categories(
    search: Optional[str] = Query(None, description="Search by category key or name"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns a list of all active service categories.
    Available to all authenticated users.
    """
    query = select(ServiceCategory).order_by(ServiceCategory.base_visit_charge.asc())

    if search:
        search_pattern = f"%{search.strip()}%"
        query = query.where(
            ServiceCategory.key.ilike(search_pattern) | ServiceCategory.name.ilike(search_pattern)
        )

    result = await db.execute(query)
    categories = result.scalars().all()

    return [ServiceCategoryResponse.model_validate(c) for c in categories]


@router.get(
    "/{category_id}",
    response_model=ServiceCategoryResponse,
    summary="Get service category by ID",
)
async def get_service_category(
    category_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns a single service category by UUID.
    """
    result = await db.execute(
        select(ServiceCategory).where(ServiceCategory.id == category_id)
    )
    category = result.scalar_one_or_none()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service category with id '{category_id}' not found.",
        )

    return ServiceCategoryResponse.model_validate(category)
