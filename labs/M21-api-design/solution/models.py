"""
M21: API Request/Response Models — Solution
Pydantic models defining the API contract for the UCC research agent.
"""

from pydantic import BaseModel, Field
from typing import Optional


class QueryRequest(BaseModel):
    """Request body for the /query and /query/stream endpoints."""
    query: str = Field(..., min_length=1, description="The user's natural-language question about UCC filings")
    session_id: Optional[str] = Field(default=None, description="Optional session ID for conversation continuity")
    stream: bool = Field(default=False, description="Whether to use SSE streaming response")


class QueryResponse(BaseModel):
    """Response body for the /query endpoint."""
    answer: str = Field(..., description="The agent's natural-language response")
    sources: list[str] = Field(..., description="List of filing numbers or references used")
    tokens_used: int = Field(..., description="Number of tokens consumed by the request")
    duration_ms: float = Field(..., description="Request processing time in milliseconds")
    request_id: str = Field(..., description="Unique request ID for tracing")


class HealthResponse(BaseModel):
    """Response body for the /health endpoint."""
    status: str = Field(..., description="Server status: 'ok' or 'degraded'")
    version: str = Field(..., description="API version string")
    uptime_seconds: float = Field(..., description="Seconds since server started")
    model: str = Field(..., description="Claude model the agent uses")


class StreamChunk(BaseModel):
    """One chunk of a streaming SSE response."""
    chunk: str = Field(..., description="One piece of the streamed response text")
    done: bool = Field(default=False, description="True for the final chunk")
    request_id: str = Field(..., description="Same UUID across all chunks in one stream")


class ErrorResponse(BaseModel):
    """Structured error response for API errors."""
    error: str = Field(..., description="Short error description, e.g. 'validation_error'")
    detail: Optional[str] = Field(default=None, description="Longer explanation of what went wrong")
    request_id: str = Field(..., description="UUID for tracing, even on errors")


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=== Testing Pydantic Models ===\n")

    # Test QueryRequest
    try:
        req = QueryRequest(query="Find UCC filings for Acme Corp")
        print(f"[PASS] QueryRequest: {req.model_dump_json()}")
    except Exception as e:
        print(f"[FAIL] QueryRequest: {e}")

    # Test QueryRequest rejects empty query
    try:
        bad_req = QueryRequest(query="")
        print(f"[FAIL] QueryRequest should reject empty query, got: {bad_req}")
    except Exception:
        print("[PASS] QueryRequest correctly rejects empty query")

    # Test QueryResponse
    try:
        resp = QueryResponse(
            answer="Found 3 filings for Acme Corp in New York.",
            sources=["UCC-2024-NY-0012847", "UCC-2024-NY-0012848"],
            tokens_used=1250,
            duration_ms=1823.5,
            request_id="abc-123-def"
        )
        print(f"[PASS] QueryResponse: {resp.model_dump_json()}")
    except Exception as e:
        print(f"[FAIL] QueryResponse: {e}")

    # Test HealthResponse
    try:
        health = HealthResponse(
            status="ok",
            version="1.0.0",
            uptime_seconds=3661.2,
            model="claude-sonnet-4-6"
        )
        print(f"[PASS] HealthResponse: {health.model_dump_json()}")
    except Exception as e:
        print(f"[FAIL] HealthResponse: {e}")

    # Test StreamChunk
    try:
        chunk = StreamChunk(chunk="Based on", done=False, request_id="abc-123")
        print(f"[PASS] StreamChunk: {chunk.model_dump_json()}")
    except Exception as e:
        print(f"[FAIL] StreamChunk: {e}")

    # Test ErrorResponse
    try:
        err = ErrorResponse(
            error="validation_error",
            detail="Query must not be empty",
            request_id="abc-123"
        )
        print(f"[PASS] ErrorResponse: {err.model_dump_json()}")
    except Exception as e:
        print(f"[FAIL] ErrorResponse: {e}")

    print("\n=== Model Tests Complete ===")
