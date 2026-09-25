from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.cooperatives import router as cooperatives_router
from app.api.v1.workers import router as workers_router
from app.api.v1.service_categories import router as service_categories_router
from app.api.v1.bookings import router as bookings_router
from app.api.v1.reviews import router as reviews_router
from app.api.v1.admin.verification import router as admin_verification_router
from app.api.v1.admin.workers import router as admin_workers_router
from app.api.v1.admin.bookings import router as admin_bookings_router
from app.api.v1.admin.complaints import router as admin_complaints_router
from app.api.v1.admin.welfare import router as admin_welfare_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(cooperatives_router)
api_router.include_router(workers_router)
api_router.include_router(service_categories_router)
api_router.include_router(bookings_router)
api_router.include_router(reviews_router)
api_router.include_router(admin_verification_router)
api_router.include_router(admin_workers_router)
api_router.include_router(admin_bookings_router)
api_router.include_router(admin_complaints_router)
api_router.include_router(admin_welfare_router)



@api_router.get("/health", tags=["Health"])
async def v1_health_check():
    """Versioned API v1 health check endpoint."""
    return {
        "status": "healthy",
        "api_version": "v1",
        "service": "SevaSangam API",
    }
