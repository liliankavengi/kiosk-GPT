"""
Health check endpoint.
"""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """Basic health check — confirms the server is running."""
    return {
        "status": "healthy",
        "service": "kiosk-gpt",
        "version": "0.1.0",
    }
