"""
Health Check Endpoint

Simple endpoint to verify API is running
"""
from datetime import datetime
from fastapi import APIRouter
from app.schemas.base import APIResponse
from app.utils.response import success_response
from app.core.config import settings

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=APIResponse[dict],
    summary="Health check",
    description="Check if the API is running and responsive"
)
async def health_check():
    """
    Health check endpoint
    
    Returns:
        API health status and version information
    """
    return success_response(
        data={
            "status": "healthy",
            "app_name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@router.get(
    "/ping",
    summary="Ping endpoint",
    description="Simple ping endpoint for connectivity checks"
)
async def ping():
    """
    Simple ping endpoint
    
    Returns:
        Plain text "pong"
    """
    return {"message": "pong"}