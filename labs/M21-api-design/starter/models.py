"""
M21: API Request/Response Models — Starter
Pydantic models defining the API contract for the UCC research agent.

Your task: Complete the 5 model classes below.
Each model uses Pydantic's BaseModel for automatic validation and serialization.
"""

from pydantic import BaseModel, Field
from typing import Optional


# ---------------------------------------------------------------------------
# TODO 1: QueryRequest
# Fields:
#   - query: str — the user's question (required, min length 1)
#   - session_id: Optional[str] — for conversation continuity (default None)
#   - stream: bool — whether to use SSE streaming (default False)
#
# Hint: Use Field(..., min_length=1) to reject empty strings
# ---------------------------------------------------------------------------
class QueryRequest(BaseModel):
    pass  # TODO: replace with actual fields


# ---------------------------------------------------------------------------
# TODO 2: QueryResponse
# Fields:
#   - answer: str — the agent's response text
#   - sources: list[str] — list of filing numbers or references used
#   - tokens_used: int — number of tokens consumed
#   - duration_ms: float — how long the request took in milliseconds
#   - request_id: str — UUID for request tracing
#
# Hint: All fields are required (no defaults)
# ---------------------------------------------------------------------------
class QueryResponse(BaseModel):
    pass  # TODO: replace with actual fields


# ---------------------------------------------------------------------------
# TODO 3: HealthResponse
# Fields:
#   - status: str — "ok" or "degraded"
#   - version: str — API version string (e.g., "1.0.0")
#   - uptime_seconds: float — seconds since server started
#   - model: str — which Claude model the agent uses
#
# Hint: All fields are required
# ---------------------------------------------------------------------------
class HealthResponse(BaseModel):
    pass  # TODO: replace with actual fields


# ---------------------------------------------------------------------------
# TODO 4: StreamChunk
# Fields:
#   - chunk: str — one piece of the streamed response
#   - done: bool — True for the final chunk
#   - request_id: str — same UUID across all chunks in one stream
#
# Hint: done defaults to False
# ---------------------------------------------------------------------------
class StreamChunk(BaseModel):
    pass  # TODO: replace with actual fields


# ---------------------------------------------------------------------------
# TODO 5: ErrorResponse
# Fields:
#   - error: str — short error description (e.g., "validation_error")
#   - detail: Optional[str] — longer explanation (default None)
#   - request_id: str — UUID for tracing even on errors
#
# Hint: detail is optional because not all errors have extra context
# ---------------------------------------------------------------------------
class ErrorResponse(BaseModel):
    pass  # TODO: replace with actual fields


# ---------------------------------------------------------------------------
# Self-test: run this file directly to verify your models
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
