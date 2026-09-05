"""Response schemas for the webhook and error responses."""

from typing import Literal
from pydantic import BaseModel, Field


class WebhookResponse(BaseModel):
    """Response returned by POST /webhook."""

    status: Literal["accepted", "duplicate"] = Field(
        ...,
        description="Processing status: accepted or duplicate",
    )
    incident_number: str = Field(
        ...,
        description="The incident number that was received",
    )
    detail: str = Field(
        ...,
        description="Human-readable explanation of what happened",
    )


class ErrorResponse(BaseModel):
    """Consistent error response format for all error cases."""

    error: str = Field(..., description="Error type")
    detail: str = Field(..., description="Human-readable error message")
