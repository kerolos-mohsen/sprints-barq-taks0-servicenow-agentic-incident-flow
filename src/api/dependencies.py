"""FastAPI dependency injection for shared service instances."""

from fastapi import Request

from src.services.incident_processor import IncidentProcessor


def get_processor(request: Request) -> IncidentProcessor:
    """Retrieve the IncidentProcessor from app state.

    The processor is created once during app lifespan and stored on app.state.

    Args:
        request: The incoming FastAPI request (provides access to app.state).

    Returns:
        The shared IncidentProcessor instance.
    """
    return request.app.state.processor
