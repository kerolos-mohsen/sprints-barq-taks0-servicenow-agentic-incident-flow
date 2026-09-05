"""Prompt builder — assembles the final prompt from template + KB articles + incident.

Loads knowledge-base articles from assets/kb_articles.json and formats them
into the prompt template along with incident details.
"""

import json
import logging
from pathlib import Path

from src.prompts.templates import USER_PROMPT_TEMPLATE
from src.schemas.incident import IncidentPayload

logger = logging.getLogger(__name__)

# Path to the knowledge-base articles shipped with the project
_KB_ARTICLES_PATH = Path(__file__).resolve().parent.parent.parent / "assets" / "kb_articles.json"


def load_kb_articles(path: Path = _KB_ARTICLES_PATH) -> list[dict]:
    """Load the knowledge-base articles from the JSON file.

    Args:
        path: Path to kb_articles.json. Defaults to assets/kb_articles.json.

    Returns:
        List of article dicts with 'id' and 'text' keys.

    Raises:
        FileNotFoundError: If the KB articles file does not exist.
    """
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    articles = data["articles"]
    logger.info("Loaded %d knowledge-base articles", len(articles))
    return articles


def format_kb_articles(articles: list[dict]) -> str:
    """Format KB articles into a numbered list for the prompt.

    Args:
        articles: List of article dicts with 'id' and 'text' keys.

    Returns:
        Formatted string like:
            1. Printer not printing: ...
            2. Email not sending: ...
    """
    lines = [f"{article['id']}. {article['text']}" for article in articles]
    return "\n".join(lines)


def build_user_prompt(incident: IncidentPayload, articles: list[dict]) -> str:
    """Build the complete user prompt for Gemini.

    Combines the KB articles and incident details into the prompt template.

    Args:
        incident: The validated incident payload.
        articles: The loaded KB articles.

    Returns:
        The fully assembled prompt string.
    """
    return USER_PROMPT_TEMPLATE.format(
        kb_articles=format_kb_articles(articles),
        number=incident.number,
        priority=incident.priority,
        short_description=incident.short_description,
        description=incident.description or "(no description provided)",
    )
