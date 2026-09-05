"""Incident payload schema matching the ServiceNow Business Rule output.

Field names and types match payload_contract.json exactly.
"""

from pydantic import BaseModel, Field


class IncidentPayload(BaseModel):
    """The JSON payload sent by the ServiceNow Business Rule.

    Every field name must match the Business Rule script exactly.
    See assets/payload_contract.json for the contract.
    """

    incident_sys_id: str = Field(
        ...,
        min_length=1,
        description="The sys_id of the incident record (used for write-back)",
    )
    number: str = Field(
        ...,
        pattern=r"^INC\d+$",
        description="The incident number, e.g. INC0010001",
    )
    short_description: str = Field(
        ...,
        min_length=1,
        description="One-line summary typed by the user",
    )
    description: str | None = Field(
        default="",
        description="Longer detail, may be empty",
    )
    priority: int = Field(
        ...,
        ge=1,
        le=5,
        description="Priority level: 1 (highest) to 5 (lowest)",
    )
