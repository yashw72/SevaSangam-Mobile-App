"""
Pydantic schemas for Authentication endpoints (Phone OTP, Verification, Role Selection).
"""

from typing import Optional
from pydantic import BaseModel, Field, field_validator
import re

from app.schemas.user import UserResponse
from backend.app.models.enums import UserRole


def normalize_indian_phone(phone: str) -> str:
    """
    Normalizes Indian phone numbers to E.164 (+91XXXXXXXXXX) format.
    Accepts 10-digit numbers or numbers with +91 prefix.
    """
    cleaned = re.sub(r"[\s\-\(\)]", "", phone)
    if cleaned.startswith("+91"):
        cleaned = cleaned[3:]
    elif cleaned.startswith("91") and len(cleaned) == 12:
        cleaned = cleaned[2:]
    elif cleaned.startswith("0") and len(cleaned) == 11:
        cleaned = cleaned[1:]

    if not (len(cleaned) == 10 and cleaned.isdigit()):
        raise ValueError("Invalid phone number. Must be a valid 10-digit Indian mobile number.")

    return f"+91{cleaned}"


class RequestOtpRequest(BaseModel):
    phone: str = Field(..., description="Indian mobile phone number (+91 or 10 digits)")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        return normalize_indian_phone(v)


class RequestOtpResponse(BaseModel):
    message: str
    phone: str
    mockOtp: Optional[str] = None
    expiresIn: int = 300


class VerifyOtpRequest(BaseModel):
    phone: str = Field(..., description="Indian mobile phone number")
    otp: str = Field(..., min_length=4, max_length=8, description="OTP code")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        return normalize_indian_phone(v)


class AuthTokenResponse(BaseModel):
    token: str
    tokenType: str = Field(default="bearer", alias="tokenType")
    isNewUser: bool = Field(..., alias="isNewUser")
    role: Optional[str] = None
    status: Optional[str] = None
    user: Optional[UserResponse] = None

    model_config = {
        "populate_by_name": True,
    }


class SelectRoleRequest(BaseModel):
    role: str = Field(
        ...,
        description="Role choice: 'customer' or 'worker'. Admin can NEVER be selected here.",
    )
    name: str = Field(..., min_length=2, max_length=255, description="Full name of user")
    language: Optional[str] = Field(default="en", max_length=5, description="Preferred language (en, hi, mr)")

    @field_validator("role")
    @classmethod
    def validate_role_choice(cls, v: str) -> str:
        normalized = v.strip().lower()
        if normalized == "admin":
            raise ValueError(
                "Admin accounts cannot be self-registered. They must be pre-provisioned by the cooperative."
            )
        if normalized not in ("customer", "worker"):
            raise ValueError("Role must be either 'customer' or 'worker'.")
        return normalized
