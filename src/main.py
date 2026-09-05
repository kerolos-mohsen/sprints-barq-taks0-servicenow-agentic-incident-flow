"""FastAPI application entrypoint.

Configures the app lifespan (startup/shutdown), registers middleware
and routes, and wires up all service dependencies.
"""

import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from src.api.middleware.auth import WebhookAuthMiddleware
from src.api.routes.health import router as health_router
from src.api.routes.webhook import router as webhook_router
from src.core.config import get_settings
from src.services.gemini_service import GeminiService
from src.services.incident_processor import IncidentProcessor
from src.services.servicenow_service import ServiceNowService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-5s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown.

    Startup:
        - Validate configuration (fail fast if env vars missing)
        - Create shared HTTP client
        - Initialize all services
        - Wire up the incident processor

    Shutdown:
        - Close the shared HTTP client
    """
    # --- STARTUP ---
    logger.info("Starting ServiceNow Incident Agent...")

    # Validate config — crashes here if env vars are missing
    settings = get_settings()
    logger.info("Configuration validated ✓")
    logger.info("ServiceNow instance: %s", settings.SERVICENOW_INSTANCE_URL)

    # Create shared async HTTP client (reused across all requests)
    http_client = httpx.AsyncClient(timeout=30.0)

    # Initialize services
    gemini = GeminiService(settings)
    servicenow = ServiceNowService(settings, http_client)
    processor = IncidentProcessor(gemini, servicenow)

    # Store on app.state so routes can access via dependency injection
    app.state.processor = processor
    app.state.http_client = http_client

    logger.info("All services initialized ✓")
    logger.info("Webhook ready at POST /api/v1/webhook")
    logger.info("Health check at GET /api/v1/health")

    yield  # App is running

    # --- SHUTDOWN ---
    logger.info("Shutting down...")
    await http_client.aclose()
    logger.info("HTTP client closed ✓")


# Create the FastAPI application
app = FastAPI(
    title="ServiceNow Incident Agent",
    description=(
        "Automated IT incident triage using Gemini LLM. "
        "Receives incidents from ServiceNow, classifies them "
        "(respond / ask / escalate), and writes the decision back."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# Register middleware (runs on every request)
app.add_middleware(WebhookAuthMiddleware)

# Register routes
app.include_router(health_router)
app.include_router(webhook_router)
