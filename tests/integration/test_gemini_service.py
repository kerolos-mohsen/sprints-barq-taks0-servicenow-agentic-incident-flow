"""Integration tests for GeminiService (mocking external API calls)."""

from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from src.services.gemini_service import GeminiService
from src.schemas.decision import GeminiDecision


class TestGeminiService:
    """Tests for Gemini decision fetching and parsing."""

    @patch("google.generativeai.GenerativeModel")
    @patch("google.generativeai.configure")
    @pytest.mark.asyncio
    async def test_successful_respond_decision(
        self, mock_configure, mock_model_cls, test_settings, sample_incident_payload
    ):
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = '{"decision": "respond", "message": "Restart the printer and unplug cable for 30 seconds."}'
        mock_model.generate_content_async = AsyncMock(return_value=mock_response)
        mock_model_cls.return_value = mock_model

        service = GeminiService(test_settings)
        decision = await service.get_decision(sample_incident_payload)

        assert isinstance(decision, GeminiDecision)
        assert decision.decision == "respond"
        assert "Restart the printer" in decision.message

    @patch("google.generativeai.GenerativeModel")
    @patch("google.generativeai.configure")
    @pytest.mark.asyncio
    async def test_markdown_code_fence_stripping(
        self, mock_configure, mock_model_cls, test_settings, sample_incident_payload
    ):
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = '```json\n{"decision": "ask", "message": "Are you using port 587?"}\n```'
        mock_model.generate_content_async = AsyncMock(return_value=mock_response)
        mock_model_cls.return_value = mock_model

        service = GeminiService(test_settings)
        decision = await service.get_decision(sample_incident_payload)

        assert decision.decision == "ask"
        assert "port 587" in decision.message

    @patch("google.generativeai.GenerativeModel")
    @patch("google.generativeai.configure")
    @pytest.mark.asyncio
    async def test_invalid_json_fallback_to_escalate(
        self, mock_configure, mock_model_cls, test_settings, sample_incident_payload
    ):
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "I think this is a printer issue but I am not outputting JSON."
        mock_model.generate_content_async = AsyncMock(return_value=mock_response)
        mock_model_cls.return_value = mock_model

        service = GeminiService(test_settings)
        decision = await service.get_decision(sample_incident_payload)

        assert decision.decision == "escalate"
        assert "human agent" in decision.message

    @patch("google.generativeai.GenerativeModel")
    @patch("google.generativeai.configure")
    @pytest.mark.asyncio
    async def test_gemini_api_exception_fallback(
        self, mock_configure, mock_model_cls, test_settings, sample_incident_payload
    ):
        mock_model = MagicMock()
        mock_model.generate_content_async = AsyncMock(side_effect=RuntimeError("API rate limit exceeded"))
        mock_model_cls.return_value = mock_model

        service = GeminiService(test_settings)
        decision = await service.get_decision(sample_incident_payload)

        assert decision.decision == "escalate"
        assert "could not produce a valid decision" in decision.message
