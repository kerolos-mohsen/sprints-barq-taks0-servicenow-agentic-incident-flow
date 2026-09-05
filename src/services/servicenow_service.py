"""ServiceNow REST API client — writes decisions back to incidents.

Uses httpx.AsyncClient to PATCH the incident record via the Table API.
Each decision type (respond, ask, escalate) sets different fields.
"""

import logging

import httpx

from src.core.config import Settings
from src.schemas.decision import GeminiDecision

logger = logging.getLogger(__name__)

# ServiceNow Table API endpoint template
_TABLE_API = "{base_url}/api/now/table/incident/{sys_id}"


class ServiceNowService:
    """Handles all write-back operations to ServiceNow."""

    def __init__(self, settings: Settings, http_client: httpx.AsyncClient) -> None:
        """Initialize the ServiceNow service.

        Args:
            settings: Application settings with instance URL and credentials.
            http_client: Shared async HTTP client (managed by app lifespan).
        """
        self._base_url = settings.SERVICENOW_INSTANCE_URL.rstrip("/")
        self._auth = (settings.SERVICENOW_USERNAME, settings.SERVICENOW_PASSWORD)
        self._client = http_client
        logger.info(
            "ServiceNowService initialized for %s", self._base_url
        )

    def _build_update_body(self, decision: GeminiDecision) -> dict:
        """Build the PATCH request body based on the decision type.

        Args:
            decision: The Gemini triage decision.

        Returns:
            Dict of fields to update on the incident.

        See pdi_guide.md Step 5 for the field mapping:
        - respond → work_notes + close_notes + close_code + state=6 (Resolved)
        - ask     → comments (customer-visible)
        - escalate → work_notes (internal note)
        """
        if decision.decision == "respond":
            return {
                "comments": f"[AI Agent] Solution:\n\n{decision.message}",
                "work_notes": f"[AI Agent] Solution: {decision.message}",
                "close_notes": decision.message,
                "close_code": "Solution provided",
                "state": "6",  # Resolved
            }
        elif decision.decision == "ask":
            return {
                "comments": (
                    f"[AI Agent] We need more information to help you:\n\n"
                    f"{decision.message}"
                ),
            }
        else:  # escalate
            return {
                "work_notes": (
                    f"[AI Agent] Escalated to human agent:\n\n"
                    f"{decision.message}"
                ),
            }

    async def update_incident(
        self, incident_sys_id: str, decision: GeminiDecision, incident_number: str
    ) -> None:
        """Write the decision back to the ServiceNow incident.

        Args:
            incident_sys_id: The sys_id of the incident to update.
            decision: The Gemini triage decision.
            incident_number: The incident number for logging.

        Raises:
            httpx.HTTPStatusError: If ServiceNow returns a non-2xx status.
        """
        url = _TABLE_API.format(base_url=self._base_url, sys_id=incident_sys_id)
        body = self._build_update_body(decision)

        logger.info(
            "[%s] Writing back decision '%s' to ServiceNow",
            incident_number,
            decision.decision,
        )

        response = await self._client.patch(
            url,
            json=body,
            auth=self._auth,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        response.raise_for_status()

        logger.info(
            "[%s] ServiceNow updated successfully (status=%d)",
            incident_number,
            response.status_code,
        )
