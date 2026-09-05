"""Integration tests for IncidentProcessor pipeline."""

from unittest.mock import AsyncMock
import pytest

from src.schemas.decision import GeminiDecision
from src.services.incident_processor import IncidentProcessor


class TestIncidentProcessor:
    """Tests for incident processor triage pipeline."""

    @pytest.mark.asyncio
    async def test_process_happy_path(self, sample_incident_payload):
        mock_gemini = AsyncMock()
        mock_gemini.get_decision.return_value = GeminiDecision(
            decision="respond", message="Restart printer"
        )
        mock_servicenow = AsyncMock()

        processor = IncidentProcessor(mock_gemini, mock_servicenow)
        await processor.process(sample_incident_payload)

        mock_gemini.get_decision.assert_called_once_with(sample_incident_payload)
        mock_servicenow.update_incident.assert_called_once_with(
            incident_sys_id=sample_incident_payload.incident_sys_id,
            decision=mock_gemini.get_decision.return_value,
            incident_number=sample_incident_payload.number,
        )

    @pytest.mark.asyncio
    async def test_process_failure_triggers_safe_escalate(
        self, sample_incident_payload
    ):
        mock_gemini = AsyncMock()
        mock_gemini.get_decision.side_effect = RuntimeError("Service breakdown")
        mock_servicenow = AsyncMock()

        processor = IncidentProcessor(mock_gemini, mock_servicenow)
        await processor.process(sample_incident_payload)

        # ServiceNow should be called with fallback escalate
        mock_servicenow.update_incident.assert_called_once()
        call_kwargs = mock_servicenow.update_incident.call_args[1]
        assert call_kwargs["incident_sys_id"] == sample_incident_payload.incident_sys_id
        assert call_kwargs["decision"].decision == "escalate"
        assert "Service breakdown" in call_kwargs["decision"].message
