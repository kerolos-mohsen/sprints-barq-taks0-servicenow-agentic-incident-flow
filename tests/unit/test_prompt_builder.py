"""Unit tests for prompt builder and template formatting."""

from src.prompts.builder import build_user_prompt, format_kb_articles, load_kb_articles
from src.schemas.incident import IncidentPayload


class TestPromptBuilder:
    """Tests for prompt assembling logic."""

    def test_load_kb_articles(self):
        articles = load_kb_articles()
        assert isinstance(articles, list)
        assert len(articles) == 5
        assert articles[0]["id"] == 1
        assert "Printer" in articles[0]["text"]

    def test_format_kb_articles(self, sample_kb_articles):
        formatted = format_kb_articles(sample_kb_articles)
        assert "1. Printer not printing" in formatted
        assert "2. Email not sending" in formatted
        assert "3. Cannot access system" in formatted

    def test_build_user_prompt_contains_all_fields(
        self, sample_incident_payload, sample_kb_articles
    ):
        prompt = build_user_prompt(sample_incident_payload, sample_kb_articles)

        assert "INC0010001" in prompt
        assert "Priority: 3" in prompt
        assert "Printer not printing after office move" in prompt
        assert "It was working yesterday" in prompt
        assert "1. Printer not printing" in prompt
        assert '{"decision": "<respond|ask|escalate>", "message": "<your message>"}' in prompt

    def test_build_user_prompt_handles_empty_description(self, sample_kb_articles):
        payload = IncidentPayload(
            incident_sys_id="1c741bd70b2322007518478d83673af3",
            number="INC0010002",
            short_description="Network glitch",
            description=None,
            priority=1,
        )
        prompt = build_user_prompt(payload, sample_kb_articles)
        assert "(no description provided)" in prompt
