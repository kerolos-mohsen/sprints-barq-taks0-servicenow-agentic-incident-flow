"""Incident processor — orchestrates the triage flow.

Handles deduplication, calls Gemini for a decision,
and writes the result back to ServiceNow.
"""

import logging

from src.schemas.decision import GeminiDecision
from src.schemas.incident import IncidentPayload
from src.services.gemini_service import GeminiService
from src.services.servicenow_service import ServiceNowService

logger = logging.getLogger(__name__)


class IncidentProcessor:
    """Orchestrates the incident triage pipeline.

    Flow: dedup check → Gemini decision → ServiceNow write-back.
    Uses an in-memory set for deduplication (FR5).
    """

    def __init__(
        self, gemini: GeminiService, servicenow: ServiceNowService
    ) -> None:
        """Initialize the processor with its service dependencies.

        Args:
            gemini: The Gemini LLM service.
            servicenow: The ServiceNow write-back service.
        """
        self._seen: set[str] = set()
        self._gemini = gemini
        self._servicenow = servicenow

    def is_duplicate(self, incident_sys_id: str) -> bool:
        """Check if this incident has already been seen.

        Args:
            incident_sys_id: The unique sys_id of the incident.

        Returns:
            True if the incident was already processed or is being processed.
        """
        return incident_sys_id in self._seen

    def mark_seen(self, incident_sys_id: str) -> None:
        """Mark an incident as seen to prevent duplicate processing.

        Args:
            incident_sys_id: The unique sys_id of the incident.
        """
        self._seen.add(incident_sys_id)

    async def process(self, payload: IncidentPayload) -> None:
        """Run the full triage pipeline for an incident.

        1. Get decision from Gemini
        2. Write decision back to ServiceNow
        3. If anything fails, attempt a safe escalation

        Args:
            payload: The validated incident payload.
        """
        try:
            logger.info("[%s] Starting triage processing", payload.number)

            # Step 1: Get AI decision
            decision = await self._gemini.get_decision(payload)

            # Step 2: Write back to ServiceNow
            await self._servicenow.update_incident(
                incident_sys_id=payload.incident_sys_id,
                decision=decision,
                incident_number=payload.number,
            )

            logger.info(
                "[%s] Triage complete: decision=%s",
                payload.number,
                decision.decision,
            )

        except Exception as exc:
            logger.error(
                "[%s] Processing failed: %s", payload.number, exc, exc_info=True
            )
            # Safe fallback: try to escalate so the ticket isn't stuck
            await self._safe_escalate(payload, str(exc))

    async def _safe_escalate(
        self, payload: IncidentPayload, error_msg: str
    ) -> None:
        """Attempt to escalate an incident after a processing failure.

        This is a last-resort fallback so the ticket doesn't go unnoticed.

        Args:
            payload: The incident payload.
            error_msg: The error message that caused the failure.
        """
        try:
            fallback = GeminiDecision(
                decision="escalate",
                message=(
                    f"Automatically escalated due to processing error: {error_msg}. "
                    f"A human agent should review this incident."
                ),
            )
            await self._servicenow.update_incident(
                incident_sys_id=payload.incident_sys_id,
                decision=fallback,
                incident_number=payload.number,
            )
            logger.info(
                "[%s] Safe escalation completed", payload.number
            )
        except Exception as fallback_exc:
            logger.error(
                "[%s] Safe escalation also failed: %s",
                payload.number,
                fallback_exc,
            )
