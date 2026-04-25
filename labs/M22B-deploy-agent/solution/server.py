"""
M22B — FastAPI Server for the UCC Agent (Solution)
=====================================================
Wraps the UCC Filing Research Agent as a REST API with three endpoints:
  - GET  /health        — health check
  - POST /query         — synchronous query
  - POST /query/stream  — streaming query via Server-Sent Events (SSE)

Run locally:
    uvicorn server:app --reload --port 8000
"""

import os
import time
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from models import (
    QueryRequest,
    QueryResponse,
    HealthResponse,
    ErrorResponse,
    FilingSummary,
    RiskSummary,
)
from mock_agent import MockUCCAgent

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
VERSION = "1.0.0"

# We use the mock agent so the lab works without an API key.
# In production, you'd swap this for the real M15B agent.
agent = MockUCCAgent()


# ---------------------------------------------------------------------------
# TODO 1: Create the FastAPI app  [SOLUTION]
# ---------------------------------------------------------------------------

app = FastAPI(
    title="UCC Filing Research Agent API",
    description=(
        "REST API for researching UCC (Uniform Commercial Code) filings. "
        "Supports synchronous queries, streaming via Server-Sent Events, "
        "and risk analysis. Built in M22B of the Claude Agent Course."
    ),
    version=VERSION,
)


# ---------------------------------------------------------------------------
# TODO 2: Add CORS middleware  [SOLUTION]
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # Allow all origins (restrict in production)
    allow_credentials=True,
    allow_methods=["*"],       # Allow all HTTP methods
    allow_headers=["*"],       # Allow all headers
)


# ---------------------------------------------------------------------------
# TODO 3: GET /health endpoint  [SOLUTION]
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint. Returns service status and metadata."""
    return HealthResponse(
        status="healthy",
        version=VERSION,
        environment=ENVIRONMENT,
        mock_mode=True,
        timestamp=datetime.utcnow().isoformat(),
    )


# ---------------------------------------------------------------------------
# TODO 4: POST /query endpoint (synchronous)  [SOLUTION]
# ---------------------------------------------------------------------------

@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    Process a UCC filing research query synchronously.

    Accepts a natural-language query about UCC filings and returns
    structured results including filing summaries and optional risk analysis.
    """
    try:
        result = agent.query(
            query=request.query,
            state=request.state,
            include_risk=request.include_risk,
            max_results=request.max_results,
        )

        # Convert raw filing dicts to Pydantic models
        filings = [FilingSummary(**f) for f in result["filings"]]

        # Convert risk dict to Pydantic model (if present)
        risk = RiskSummary(**result["risk"]) if result.get("risk") else None

        return QueryResponse(
            query=request.query,
            answer=result["answer"],
            filings=filings,
            risk=risk,
            processing_time_ms=result["processing_time_ms"],
            mock_mode=True,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Agent query failed: {str(e)}",
        )


# ---------------------------------------------------------------------------
# TODO 5: POST /query/stream endpoint (Server-Sent Events)  [SOLUTION]
# ---------------------------------------------------------------------------

@app.post("/query/stream")
async def query_stream(request: QueryRequest):
    """
    Process a UCC filing research query with streaming response.

    Returns Server-Sent Events (SSE) with real-time chunks:
      - event: chunk  — text fragment of the answer
      - event: filing — structured filing summary
      - event: risk   — risk analysis result
      - event: done   — signals stream completion
    """
    def generate():
        try:
            yield from agent.query_stream(
                query=request.query,
                state=request.state,
                include_risk=request.include_risk,
                max_results=request.max_results,
            )
        except Exception as e:
            import json
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


# ---------------------------------------------------------------------------
# Run with: python server.py
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=True)
