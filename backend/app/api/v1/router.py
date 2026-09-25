from fastapi import APIRouter

api_router = APIRouter()


@api_router.get("/health", tags=["Health"])
async def v1_health_check():
    """Versioned API v1 health check endpoint."""
    return {
        "status": "healthy",
        "api_version": "v1",
        "service": "SevaSangam API",
    }
