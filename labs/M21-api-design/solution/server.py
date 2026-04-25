"""
M21: UCC Agent API Server — Solution
FastAPI application wrapping the UCC research agent.

Run with:  python server.py
Test with: bash test_api.sh
Docs at:   http://localhost:8000/docs
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
import uvicorn
import time
import uuid
import json
import traceback

from models import QueryRequest, QueryResponse, HealthResponse, StreamChunk, ErrorResponse
from mock_agent import mock_query, mock_stream

START_TIME = time.time()

# ---------------------------------------------------------------------------
# 1. Create FastAPI app with metadata
# ---------------------------------------------------------------------------
app = FastAPI(
    title="UCC Research Agent API",
    version="1.0.0",
    description=(
        "Production API for the UCC (Uniform Commercial Code) research agent. "
        "Search UCC filings, assess lien risk, and resolve entity names using "
        "an AI-powered agent backed by Claude."
    ),
)

# ---------------------------------------------------------------------------
# 2. Add CORS middleware
#
# allow_origins=["*"] is acceptable for development and testing.
# In production, replace with your actual frontend domains:
#   allow_origins=["https://app.yourcompany.com"]
#
# Why CORS matters: Without this middleware, browsers will block requests
# from any frontend hosted on a different domain. The server must explicitly
# opt in to cross-origin access.
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # DEV ONLY — lock down in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# 3. GET /health endpoint
# ---------------------------------------------------------------------------
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint for load balancers and monitoring.

    Returns server status, version, uptime, and the model in use.
    Used by Docker HEALTHCHECK, Kubernetes liveness probes, and
    external monitoring services.
    """
    return HealthResponse(
        status="ok",
        version=app.version,
        uptime_seconds=round(time.time() - START_TIME, 2),
        model="claude-sonnet-4-20250514",
    )


# ---------------------------------------------------------------------------
# 4. POST /query endpoint
# ---------------------------------------------------------------------------
@app.post("/query", response_model=QueryResponse)
async def query_agent(request: QueryRequest):
    """
    Synchronous query endpoint.

    Sends the user's question to the UCC research agent and returns
    the complete response with sources, token usage, and timing.
    """
    request_id = str(uuid.uuid4())

    # Validate query (Pydantic min_length handles empty strings, but
    # we add an explicit check for whitespace-only queries)
    if not request.query.strip():
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                error="validation_error",
                detail="Query must contain non-whitespace characters",
                request_id=request_id,
            ).model_dump(),
        )

    try:
        start = time.time()
        result = mock_query(request.query)
        duration_ms = round((time.time() - start) * 1000, 2)

        return QueryResponse(
            answer=result["answer"],
            sources=result["sources"],
            tokens_used=result["tokens_used"],
            duration_ms=duration_ms,
            request_id=request_id,
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error="internal_error",
                detail=str(e),
                request_id=request_id,
            ).model_dump(),
        )


# ---------------------------------------------------------------------------
# 5. POST /query/stream endpoint (SSE)
# ---------------------------------------------------------------------------
@app.post("/query/stream")
async def query_agent_stream(request: QueryRequest):
    """
    Streaming query endpoint using Server-Sent Events (SSE).

    Returns chunks of the agent's response as they are generated.
    Each chunk follows the SSE format:  data: {json}\\n\\n

    The final chunk has done=true to signal completion.
    """
    request_id = str(uuid.uuid4())

    if not request.query.strip():
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                error="validation_error",
                detail="Query must contain non-whitespace characters",
                request_id=request_id,
            ).model_dump(),
        )

    async def event_generator():
        try:
            for chunk_text in mock_stream(request.query):
                chunk = StreamChunk(
                    chunk=chunk_text,
                    done=False,
                    request_id=request_id,
                )
                yield f"data: {chunk.model_dump_json()}\n\n"

            # Final chunk signals completion
            final = StreamChunk(
                chunk="",
                done=True,
                request_id=request_id,
            )
            yield f"data: {final.model_dump_json()}\n\n"

        except Exception as e:
            error = ErrorResponse(
                error="stream_error",
                detail=str(e),
                request_id=request_id,
            )
            yield f"data: {error.model_dump_json()}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Request-ID": request_id,
        },
    )


# ---------------------------------------------------------------------------
# 6. Global exception handler
# ---------------------------------------------------------------------------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Catch-all exception handler.

    Ensures every error returns a structured JSON response with a
    request_id for tracing — never a raw stack trace.
    """
    request_id = str(uuid.uuid4())
    print(f"[ERROR] {request_id}: {exc}")
    traceback.print_exc()

    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="internal_error",
            detail=str(exc),
            request_id=request_id,
        ).model_dump(),
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print(f"Starting UCC Agent API v{app.version}")
    print(f"Docs: http://localhost:8000/docs")
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
