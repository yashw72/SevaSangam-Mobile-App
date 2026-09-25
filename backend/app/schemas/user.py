"""
Pydantic schemas for User.

Response schemas use camelCase aliases to match the mobile API contract.
"""

from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime

from backend.app.models.enums import UserRole


# ── Base / shared fields ────────────────────────────────────────────────────

class UserBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    phone: str = Field(..., min_length=10, max_length=15)
    language: str = Field(default="en", max_length=5)
    avatar: Optional[str] = None


# ── Create ──────────────────────────────────────────────────────────────────

class UserCreate(UserBase):
    role: UserRole


# ── Update ──────────────────────────────────────────────────────────────────

class UserUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    phone: Optional[str] = Field(default=None, min_length=10, max_length=15)
    language: Optional[str] = Field(default=None, max_length=5)
    avatar: Optional[str] = None


# ── Response ────────────────────────────────────────────────────────────────

class UserResponse(UserBase):
    id: UUID
    role: UserRole
    created_at: Optional[datetime] = Field(default=None, alias="createdAt")
    updated_at: Optional[datetime] = Field(default=None, alias="updatedAt")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }
