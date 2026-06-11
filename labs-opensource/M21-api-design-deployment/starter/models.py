"""
M21 Lab: Request/Response Contracts (COMPLETE)
===============================================
Pydantic models — FastAPI validates inputs and generates OpenAPI docs
from these automatically.
"""

import uuid
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class AgentRequest(BaseModel):
    """What clients POST to /agent/run."""

    query: str = Field(..., min_length=1, max_length=4096)
    session_id: Optional[str] = Field(
        default=None, description="UUID from a previous response to continue the conversation"
    )
    max_iterations: int = Field(default=8, ge=1, le=20)
    stream: bool = False

    @field_validator("query")
    @classmethod
    def strip_and_check(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("query must not be empty after stripping whitespace")
        return v


class ToolCallRecord(BaseModel):
    """One tool invocation captured from the agent loop."""

    tool_name: str
    input_summary: str    # truncated for log safety
    output_summary: str
    duration_ms: int


class AgentResponse(BaseModel):
    """Successful synchronous agent response."""

    result: str
    session_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Use this in the next request to continue the conversation",
    )
    iterations: int = Field(description="Agent loop iterations used")
    tool_calls: List[ToolCallRecord] = Field(default_factory=list)
    latency_ms: int = Field(description="Total wall-clock time")
    model: str = Field(description="Ollama model used")


class ErrorResponse(BaseModel):
    """Standard error envelope returned on 4xx/5xx."""

    error: str
    detail: Optional[str] = None
    request_id: Optional[str] = None
