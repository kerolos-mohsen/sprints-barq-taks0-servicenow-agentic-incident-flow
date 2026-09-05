"""Webhook authentication middleware.

Validates the X-Webhook-Secret header on POST /webhook requests.
All other routes pass through without authentication.
"""

import logging

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse

from src.core.config import get_settings
from src.core.security import verify_webhook_secret

logger = logging.getLogger(__name__)


class WebhookAuthMiddleware(BaseHTTPMiddleware):
    """Middleware that authenticates webhook requests via a shared secret.

    Only POST /webhook requires authentication.
    Other endpoints (e.g., GET /health) pass through freely.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Check the shared secret on webhook requests.

        Args:
            request: The incoming HTTP request.
            call_next: The next middleware/handler in the chain.

        Returns:
            401 JSONResponse if auth fails, otherwise the normal response.
        """
        if request.method == "POST" and request.url.path == "/api/v1/webhook":
            provided_secret = request.headers.get("X-Webhook-Secret")
            expected_secret = get_settings().WEBHOOK_SECRET

            if not verify_webhook_secret(provided_secret, expected_secret):
                logger.warning(
                    "Unauthorized webhook attempt from %s", request.client.host
                )
                return JSONResponse(
                    status_code=401,
                    content={
                        "error": "Unauthorized",
                        "detail": "Invalid or missing X-Webhook-Secret header",
                    },
                )

        return await call_next(request)
