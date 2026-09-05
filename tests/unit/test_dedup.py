"""Unit tests for incident deduplication guard."""

from unittest.mock import AsyncMock

from src.services.incident_processor import IncidentProcessor


class TestDeduplication:
    """Tests for in-memory deduplication set."""

    def test_new_incident_not_duplicate(self):
        processor = IncidentProcessor(gemini=AsyncMock(), servicenow=AsyncMock())
        assert processor.is_duplicate("sys_id_001") is False

    def test_marked_incident_is_duplicate(self):
        processor = IncidentProcessor(gemini=AsyncMock(), servicenow=AsyncMock())
        processor.mark_seen("sys_id_001")
        assert processor.is_duplicate("sys_id_001") is True

    def test_different_incident_not_affected(self):
        processor = IncidentProcessor(gemini=AsyncMock(), servicenow=AsyncMock())
        processor.mark_seen("sys_id_001")
        assert processor.is_duplicate("sys_id_002") is False

    def test_multiple_incidents_deduplicated_independently(self):
        processor = IncidentProcessor(gemini=AsyncMock(), servicenow=AsyncMock())
        processor.mark_seen("sys_1")
        processor.mark_seen("sys_2")

        assert processor.is_duplicate("sys_1") is True
        assert processor.is_duplicate("sys_2") is True
        assert processor.is_duplicate("sys_3") is False
