"""Webhook authentication helpers.

Provides constant-time secret comparison to prevent timing attacks.
"""

import hmac


def verify_webhook_secret(provided: str | None, expected: str) -> bool:
    """Check if the provided secret matches the expected secret.

    Uses hmac.compare_digest for constant-time comparison,
    preventing timing-based side-channel attacks.

    Args:
        provided: The secret from the incoming request header.
        expected: The secret from our environment config.

    Returns:
        True if secrets match, False otherwise.
    """
    if provided is None:
        return False
    return hmac.compare_digest(provided.encode(), expected.encode())
