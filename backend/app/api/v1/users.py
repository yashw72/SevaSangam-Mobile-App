"""
Users Router for SevaSangam API.

Endpoints:
  GET    /users/me     — Authenticated user's own profile
  PATCH  /users/me     — Update own profile
  GET    /users        — Admin-only paginated user list
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user, require_role
from app.db.session import get_db
from backend.app.models.user import User
from backend.app.models.enums import UserRole
from app.schemas.user import UserResponse, UserUpdate

logger = logging.getLogger("sevasangam.users")

router = APIRouter(prefix="/users", tags=["Users"])


# ── Paginated list response shape ───────────────────────────────────────────
# Matches the mobile contract: { data, page, limit, total, totalPages }

def paginated_response(data: list, page: int, limit: int, total: int) -> dict:
    """Build a standard paginated response envelope."""
    return {
        "data": data,
        "page": page,
        "limit": limit,
        "total": total,
        "totalPages": max(1, (total + limit - 1) // limit),
    }


# ── GET /users/me ───────────────────────────────────────────────────────────

@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user's profile",
)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
):
    """
    Returns the authenticated user's profile details.
    """
    return UserResponse.model_validate(current_user)


# ── PATCH /users/me ─────────────────────────────────────────────────────────

@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Update current user's profile",
)
async def update_current_user_profile(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Allows the authenticated user to update their own profile fields.
    Only non-null fields in the payload are applied.
    """
    update_data = payload.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update were provided.",
        )

    # Apply each provided field
    for field, value in update_data.items():
        setattr(current_user, field, value)

    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)

    logger.info(f"[USERS] Updated profile for user {current_user.id}: {list(update_data.keys())}")

    return UserResponse.model_validate(current_user)


# ── GET /users (Admin only) ────────────────────────────────────────────────

@router.get(
    "",
    summary="List all users (admin only)",
)
async def list_users(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    role: Optional[str] = Query(None, description="Filter by role: customer, worker, admin"),
    search: Optional[str] = Query(None, description="Search by name or phone (partial match)"),
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns a paginated list of all users. Admin access only.
    Supports optional role filter and name/phone search.
    """
    # Build base query
    query = select(User)
    count_query = select(func.count(User.id))

    # Apply role filter
    if role:
        role_lower = role.strip().lower()
        try:
            role_enum = UserRole(role_lower)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role filter '{role}'. Must be one of: customer, worker, admin.",
            )
        query = query.where(User.role == role_enum)
        count_query = count_query.where(User.role == role_enum)

    # Apply search filter (name or phone partial match)
    if search:
        search_pattern = f"%{search.strip()}%"
        search_filter = User.name.ilike(search_pattern) | User.phone.ilike(search_pattern)
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Apply pagination
    offset = (page - 1) * limit
    query = query.order_by(User.created_at.desc()).offset(offset).limit(limit)

    result = await db.execute(query)
    users = result.scalars().all()

    user_responses = [UserResponse.model_validate(u) for u in users]

    logger.info(f"[USERS] Admin {current_user.id} listed users: page={page}, total={total}")

    return paginated_response(
        data=user_responses,
        page=page,
        limit=limit,
        total=total,
    )
