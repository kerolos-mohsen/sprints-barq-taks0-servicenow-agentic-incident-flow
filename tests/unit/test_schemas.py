"""Unit tests for Pydantic data validation schemas."""

import pytest
from pydantic import ValidationError

from src.schemas.decision import GeminiDecision
from src.schemas.incident import IncidentPayload
from src.schemas.responses import ErrorResponse, WebhookResponse


class TestIncidentPayload:
    """Tests for IncidentPayload validation."""

    def test_valid_incident_payload(self):
        payload = IncidentPayload(
            incident_sys_id="1c741bd70b2322007518478d83673af3",
            number="INC0010001",
            short_description="Printer issue",
            description="Details here",
            priority=2,
        )
        assert payload.number == "INC0010001"
        assert payload.priority == 2
        assert payload.description == "Details here"

    def test_valid_payload_with_none_description(self):
        payload = IncidentPayload(
            incident_sys_id="1c741bd70b2322007518478d83673af3",
            number="INC0010002",
            short_description="Network issue",
            description=None,
            priority=1,
        )
        assert payload.description is None

    def test_invalid_incident_number_format(self):
        with pytest.raises(ValidationError):
            IncidentPayload(
                incident_sys_id="1c741bd70b2322007518478d83673af3",
                number="TICKET123",
                short_description="Bad number",
                priority=3,
            )

    def test_empty_short_description(self):
        with pytest.raises(ValidationError):
            IncidentPayload(
                incident_sys_id="1c741bd70b2322007518478d83673af3",
                number="INC0010001",
                short_description="",
                priority=3,
            )

    @pytest.mark.parametrize("invalid_priority", [0, 6, -1, 10])
    def test_invalid_priority_range(self, invalid_priority):
        with pytest.raises(ValidationError):
            IncidentPayload(
                incident_sys_id="1c741bd70b2322007518478d83673af3",
                number="INC0010001",
                short_description="Test",
                priority=invalid_priority,
            )


class TestGeminiDecision:
    """Tests for GeminiDecision validation."""

    @pytest.mark.parametrize("valid_decision", ["respond", "ask", "escalate"])
    def test_valid_decisions(self, valid_decision):
        decision = GeminiDecision(decision=valid_decision, message="Test message")
        assert decision.decision == valid_decision
        assert decision.message == "Test message"

    def test_invalid_decision_type(self):
        with pytest.raises(ValidationError):
            GeminiDecision(decision="ignore", message="Test")


class TestWebhookResponse:
    """Tests for WebhookResponse and ErrorResponse."""

    def test_valid_accepted_response(self):
        resp = WebhookResponse(
            status="accepted",
            incident_number="INC0010001",
            detail="Queued for processing",
        )
        assert resp.status == "accepted"

    def test_valid_duplicate_response(self):
        resp = WebhookResponse(
            status="duplicate",
            incident_number="INC0010001",
            detail="Already processed",
        )
        assert resp.status == "duplicate"

    def test_invalid_status(self):
        with pytest.raises(ValidationError):
            WebhookResponse(
                status="rejected",
                incident_number="INC0010001",
                detail="Not allowed",
            )

    def test_error_response(self):
        err = ErrorResponse(error="Unauthorized", detail="Invalid secret")
        assert err.error == "Unauthorized"
