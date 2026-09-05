"""Pytest configuration and shared test fixtures."""

import os
import pytest

# Set test environment variables before any module imports Settings
os.environ["GEMINI_API_KEY"] = "mock-gemini-key"
os.environ["GEMINI_MODEL"] = "gemini-3.6-flash"
os.environ["SERVICENOW_INSTANCE_URL"] = "https://devmock.service-now.com"
os.environ["SERVICENOW_USERNAME"] = "admin"
os.environ["SERVICENOW_PASSWORD"] = "mock-password"
os.environ["WEBHOOK_SECRET"] = "test-secret-12345"

from src.core.config import Settings, get_settings
from src.schemas.incident import IncidentPayload


@pytest.fixture(autouse=True)
def reset_settings_cache():
    """Clear lru_cache on get_settings between tests."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def test_settings() -> Settings:
    """Fixture providing populated Settings instance."""
    return Settings(
        GEMINI_API_KEY="mock-gemini-key",
        GEMINI_MODEL="gemini-2.0-flash",
        SERVICENOW_INSTANCE_URL="https://devmock.service-now.com",
        SERVICENOW_USERNAME="admin",
        SERVICENOW_PASSWORD="mock-password",
        WEBHOOK_SECRET="test-secret-12345",
    )


@pytest.fixture
def sample_incident_payload() -> IncidentPayload:
    """Fixture providing a standard valid incident payload."""
    return IncidentPayload(
        incident_sys_id="1c741bd70b2322007518478d83673af3",
        number="INC0010001",
        short_description="Printer not printing after office move",
        description="It was working yesterday. I tried turning it off and on.",
        priority=3,
    )


@pytest.fixture
def sample_kb_articles() -> list[dict]:
    """Fixture providing test KB articles."""
    return [
        {
            "id": 1,
            "text": "Printer not printing: Restart the printer and unplug the cable for 30 seconds.",
        },
        {
            "id": 2,
            "text": "Email not sending: Check SMTP settings and ensure port 587 is open.",
        },
        {
            "id": 3,
            "text": "Cannot access system: Reset password via the 'Forgot Password' page.",
        },
    ]
