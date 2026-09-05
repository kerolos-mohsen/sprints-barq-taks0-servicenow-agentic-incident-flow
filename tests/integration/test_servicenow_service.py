"""Integration tests for ServiceNow write-back service."""

from unittest.mock import AsyncMock, MagicMock
import httpx
import pytest

from src.schemas.decision import GeminiDecision
from src.services.servicenow_service import ServiceNowService


class TestServiceNowService:
    """Tests for ServiceNow REST API updates."""

    @pytest.mark.asyncio
    async def test_update_incident_respond(self, test_settings):
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_client.patch.return_value = mock_response

        service = ServiceNowService(test_settings, mock_client)
        decision = GeminiDecision(decision="respond", message="Printer power cycle")

        await service.update_incident(
            incident_sys_id="sys123",
            decision=decision,
            incident_number="INC001",
        )

        mock_client.patch.assert_called_once()
        call_args = mock_client.patch.call_args
        assert call_args[0][0] == "https://devmock.service-now.com/api/now/table/incident/sys123"
        json_body = call_args[1]["json"]
        assert json_body["state"] == "6"
        assert json_body["close_code"] == "Solution provided"
        assert "Printer power cycle" in json_body["close_notes"]
        assert "[AI Agent] Solution" in json_body["work_notes"]
        assert "[AI Agent] Solution" in json_body["comments"]

    @pytest.mark.asyncio
    async def test_update_incident_ask(self, test_settings):
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_client.patch.return_value = mock_response

        service = ServiceNowService(test_settings, mock_client)
        decision = GeminiDecision(decision="ask", message="Which port are you using?")

        await service.update_incident(
            incident_sys_id="sys123",
            decision=decision,
            incident_number="INC001",
        )

        json_body = mock_client.patch.call_args[1]["json"]
        assert "comments" in json_body
        assert "Which port are you using?" in json_body["comments"]
        assert "work_notes" not in json_body

    @pytest.mark.asyncio
    async def test_update_incident_escalate(self, test_settings):
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_client.patch.return_value = mock_response

        service = ServiceNowService(test_settings, mock_client)
        decision = GeminiDecision(decision="escalate", message="Human needed")

        await service.update_incident(
            incident_sys_id="sys123",
            decision=decision,
            incident_number="INC001",
        )

        json_body = mock_client.patch.call_args[1]["json"]
        assert "work_notes" in json_body
        assert "[AI Agent] Escalated to human agent" in json_body["work_notes"]
        assert "comments" not in json_body
        assert "state" not in json_body
