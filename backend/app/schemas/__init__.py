"""
Schemas package — re-export all schemas for convenience.
"""

from backend.app.schemas.user import UserCreate, UserUpdate, UserResponse
from backend.app.schemas.auth import (
    RequestOtpRequest,
    RequestOtpResponse,
    VerifyOtpRequest,
    AuthTokenResponse,
    SelectRoleRequest,
)
from backend.app.schemas.cooperative import CooperativeCreate, CooperativeUpdate, CooperativeResponse
from backend.app.schemas.worker import (
    WorkerCreate, WorkerUpdate, WorkerResponse,
    LocationSchema, InsuranceSchema,
)
from backend.app.schemas.certificate import (
    CertificateCreate, CertificateUpdate, CertificateResponse,
    OcrSchema,
)
from backend.app.schemas.service_category import (
    ServiceCategoryCreate, ServiceCategoryUpdate, ServiceCategoryResponse,
)
from backend.app.schemas.booking import (
    BookingCreate, BookingUpdate, BookingResponse,
    AddressSchema, TimelineEntry,
)
from backend.app.schemas.review import ReviewCreate, ReviewUpdate, ReviewResponse
from backend.app.schemas.complaint import ComplaintCreate, ComplaintUpdate, ComplaintResponse
from backend.app.schemas.welfare_program import (
    WelfareProgramCreate, WelfareProgramUpdate, WelfareProgramResponse,
)
from backend.app.schemas.earning import EarningCreate, EarningUpdate, EarningResponse
from backend.app.schemas.notification import NotificationCreate, NotificationUpdate, NotificationResponse

__all__ = [
    # User
    "UserCreate", "UserUpdate", "UserResponse",
    # Cooperative
    "CooperativeCreate", "CooperativeUpdate", "CooperativeResponse",
    # Worker
    "WorkerCreate", "WorkerUpdate", "WorkerResponse",
    "LocationSchema", "InsuranceSchema",
    # Certificate
    "CertificateCreate", "CertificateUpdate", "CertificateResponse",
    "OcrSchema",
    # ServiceCategory
    "ServiceCategoryCreate", "ServiceCategoryUpdate", "ServiceCategoryResponse",
    # Booking
    "BookingCreate", "BookingUpdate", "BookingResponse",
    "AddressSchema", "TimelineEntry",
    # Review
    "ReviewCreate", "ReviewUpdate", "ReviewResponse",
    # Complaint
    "ComplaintCreate", "ComplaintUpdate", "ComplaintResponse",
    # WelfareProgram
    "WelfareProgramCreate", "WelfareProgramUpdate", "WelfareProgramResponse",
    # Earning
    "EarningCreate", "EarningUpdate", "EarningResponse",
    # Notification
    "NotificationCreate", "NotificationUpdate", "NotificationResponse",
]
