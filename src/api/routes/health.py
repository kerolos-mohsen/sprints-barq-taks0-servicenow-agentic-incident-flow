"""Health check endpoint.

Returns service status and configuration state.
Not protected by authentication — used for quick liveness checks.
"""

from fastapi import APIRouter

from src.core.config import get_settings

router = APIRouter(prefix="/api/v1", tags=["health"])


@router.get("/health")
async def health_check() -> dict:
    """Check if the service is running and properly configured.

    Returns:
        JSON with service status and config availability.
    """
    settings = get_settings()
    return {
        "status": "ok",
        "service": "servicenow-incident-agent",
        "gemini_configured": bool(settings.GEMINI_API_KEY),
        "servicenow_configured": bool(settings.SERVICENOW_INSTANCE_URL),
    }
