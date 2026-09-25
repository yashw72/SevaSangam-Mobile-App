from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.cooperatives import router as cooperatives_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(cooperatives_router)



@api_router.get("/health", tags=["Health"])
async def v1_health_check():
    """Versioned API v1 health check endpoint."""
    return {
        "status": "healthy",
        "api_version": "v1",
        "service": "SevaSangam API",
    }
