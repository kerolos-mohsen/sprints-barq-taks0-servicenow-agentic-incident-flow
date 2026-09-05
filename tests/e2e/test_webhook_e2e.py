"""End-to-end tests for the FastAPI webhook and health endpoints."""

from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.schemas.decision import GeminiDecision
from src.services.incident_processor import IncidentProcessor


@pytest.fixture
def client():
    """TestClient for testing FastAPI endpoints."""
    with (
        patch("google.generativeai.configure"),
        patch("google.generativeai.GenerativeModel"),
    ):
        with TestClient(app) as test_client:
            yield test_client


class TestHealthEndpoint:
    """E2E tests for GET /api/v1/health."""

    def test_health_check_returns_200(self, client):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["gemini_configured"] is True
        assert data["servicenow_configured"] is True


class TestWebhookEndpointAuth:
    """E2E tests for Webhook authentication middleware."""

    def test_webhook_missing_secret_returns_401(self, client):
        payload = {
            "incident_sys_id": "sys123",
            "number": "INC0010001",
            "short_description": "Printer broken",
            "description": "Please help",
            "priority": 3,
        }
        response = client.post("/api/v1/webhook", json=payload)
        assert response.status_code == 401
        assert response.json()["error"] == "Unauthorized"

    def test_webhook_invalid_secret_returns_401(self, client):
        payload = {
            "incident_sys_id": "sys123",
            "number": "INC0010001",
            "short_description": "Printer broken",
            "description": "Please help",
            "priority": 3,
        }
        response = client.post(
            "/api/v1/webhook",
            json=payload,
            headers={"X-Webhook-Secret": "wrong-secret"},
        )
        assert response.status_code == 401


class TestWebhookEndpointPayloadValidation:
    """E2E tests for Pydantic payload validation."""

    def test_webhook_invalid_payload_returns_422(self, client):
        invalid_payload = {
            "incident_sys_id": "sys123",
            "number": "NOT_AN_INCIDENT_NUMBER",
            "short_description": "",
            "priority": 99,
        }
        response = client.post(
            "/api/v1/webhook",
            json=invalid_payload,
            headers={"X-Webhook-Secret": "test-secret-12345"},
        )
        assert response.status_code == 422


class TestWebhookFlowAndDedup:
    """E2E tests for webhook acceptance and deduplication."""

    def test_valid_webhook_accepted_and_duplicate_handled(self, client):
        mock_gemini = AsyncMock()
        mock_gemini.get_decision.return_value = GeminiDecision(
            decision="respond", message="Restart printer"
        )
        mock_sn = AsyncMock()
        test_processor = IncidentProcessor(mock_gemini, mock_sn)

        # Inject test processor into app state
        app.state.processor = test_processor

        payload = {
            "incident_sys_id": "e2e_sys_id_999",
            "number": "INC0099999",
            "short_description": "Printer issue",
            "description": "Check cable",
            "priority": 3,
        }
        headers = {"X-Webhook-Secret": "test-secret-12345"}

        # 1st call -> accepted (202)
        resp1 = client.post("/api/v1/webhook", json=payload, headers=headers)
        assert resp1.status_code == 202
        body1 = resp1.json()
        assert body1["status"] == "accepted"
        assert body1["incident_number"] == "INC0099999"

        # 2nd call with identical sys_id -> duplicate (202)
        resp2 = client.post("/api/v1/webhook", json=payload, headers=headers)
        assert resp2.status_code == 202
        body2 = resp2.json()
        assert body2["status"] == "duplicate"
        assert body2["incident_number"] == "INC0099999"
