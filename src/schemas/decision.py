"""Gemini decision schema — the structured output from the LLM."""

from typing import Literal

from pydantic import BaseModel, Field


class GeminiDecision(BaseModel):
    """The JSON response we expect from Gemini.

    - respond: article clearly solves the problem → provide solution
    - ask:     article might apply but description is too vague → clarify
    - escalate: no article covers this → send to a human
    """

    decision: Literal["respond", "ask", "escalate"] = Field(
        ...,
        description="One of: respond, ask, escalate",
    )
    message: str = Field(
        ...,
        min_length=1,
        description="The solution, clarifying question, or escalation reason",
    )
