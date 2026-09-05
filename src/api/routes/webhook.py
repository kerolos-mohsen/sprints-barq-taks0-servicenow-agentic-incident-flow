"""Webhook endpoint — receives incidents from ServiceNow.

Validates the payload, checks for duplicates, and queues
background processing (Gemini decision + ServiceNow write-back).
Returns 202 Accepted immediately so ServiceNow doesn't timeout.
"""

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, Header

from src.api.dependencies import get_processor
from src.schemas.incident import IncidentPayload
from src.schemas.responses import WebhookResponse
from src.services.incident_processor import IncidentProcessor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["webhook"])


@router.post("/webhook", status_code=202, response_model=WebhookResponse)
async def receive_incident(
    payload: IncidentPayload,
    background_tasks: BackgroundTasks,
    x_webhook_secret: str | None = Header(
        None,
        alias="X-Webhook-Secret",
        description="Shared secret configured in .env (e.g. task0-secret-key-2026)",
    ),
    processor: IncidentProcessor = Depends(get_processor),
) -> WebhookResponse:
    """Receive an incident from the ServiceNow Business Rule.

    Flow:
    1. Pydantic validates the payload automatically (422 on failure)
    2. Auth middleware already validated X-Webhook-Secret (401 on failure)
    3. Check dedup — if already seen, return 202 with "duplicate"
    4. Mark as seen, queue background task, return 202 "accepted"

    The Gemini call and ServiceNow write-back happen in the background
    so this endpoint responds in under 2 seconds (NFR1).

    Args:
        payload: The validated incident data from ServiceNow.
        background_tasks: FastAPI's background task queue.
        processor: The shared IncidentProcessor instance.

    Returns:
        202 response with processing status.
    """
    # Check for duplicate
    if processor.is_duplicate(payload.incident_sys_id):
        logger.info("[%s] Duplicate incident, skipping", payload.number)
        return WebhookResponse(
            status="duplicate",
            incident_number=payload.number,
            detail="Incident already being processed",
        )

    # Mark as seen and queue for background processing
    processor.mark_seen(payload.incident_sys_id)
    background_tasks.add_task(processor.process, payload)

    logger.info("[%s] Incident accepted and queued", payload.number)
    return WebhookResponse(
        status="accepted",
        incident_number=payload.number,
        detail="Incident queued for AI triage",
    )
