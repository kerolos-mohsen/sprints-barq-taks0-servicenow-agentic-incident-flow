"""Gemini LLM service — sends incidents to Gemini and parses decisions.

Uses the google-generativeai SDK to call the Gemini API.
Falls back to 'escalate' if the response cannot be parsed.
"""

import json
import logging

import google.generativeai as genai

from src.core.config import Settings
from src.prompts.builder import build_user_prompt, load_kb_articles
from src.prompts.templates import SYSTEM_PROMPT
from src.schemas.decision import GeminiDecision
from src.schemas.incident import IncidentPayload

logger = logging.getLogger(__name__)


class GeminiService:
    """Handles all interactions with the Gemini LLM API."""

    def __init__(self, settings: Settings) -> None:
        """Initialize the Gemini service.

        Args:
            settings: Application settings containing the API key and model name.
        """
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self._model = genai.GenerativeModel(
            model_name=settings.GEMINI_MODEL,
            system_instruction=SYSTEM_PROMPT,
        )
        self._articles = load_kb_articles()
        logger.info(
            "GeminiService initialized with model=%s", settings.GEMINI_MODEL
        )

    async def get_decision(self, incident: IncidentPayload) -> GeminiDecision:
        """Send an incident to Gemini and return the triage decision.

        Args:
            incident: The validated incident payload.

        Returns:
            A GeminiDecision with the decision and message.
            Falls back to 'escalate' if parsing fails.
        """
        prompt = build_user_prompt(incident, self._articles)
        logger.info("[%s] Sending to Gemini for triage", incident.number)

        try:
            response = self._model.generate_content(prompt)
            raw_text = response.text.strip()
            logger.info("[%s] Gemini raw response: %s", incident.number, raw_text)

            # Strip markdown code fences if Gemini wraps the JSON
            cleaned = raw_text
            if cleaned.startswith("```"):
                # Remove ```json or ``` prefix and ``` suffix
                lines = cleaned.split("\n")
                lines = [
                    line
                    for line in lines
                    if not line.strip().startswith("```")
                ]
                cleaned = "\n".join(lines).strip()

            parsed = json.loads(cleaned)
            decision = GeminiDecision(**parsed)
            logger.info(
                "[%s] Gemini decision: %s", incident.number, decision.decision
            )
            return decision

        except (json.JSONDecodeError, KeyError, ValueError, Exception) as exc:
            logger.error(
                "[%s] Failed to parse Gemini response: %s", incident.number, exc
            )
            return GeminiDecision(
                decision="escalate",
                message=(
                    "Automatically escalated: AI could not produce a valid "
                    "decision. A human agent should review this incident."
                ),
            )
