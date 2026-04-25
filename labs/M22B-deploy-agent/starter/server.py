"""
M22B — FastAPI Server for the UCC Agent (Starter — complete the TODOs)
=========================================================================
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
# TODO 1: Create the FastAPI app
# ---------------------------------------------------------------------------
# Create a FastAPI instance with:
#   - title: "UCC Filing Research Agent API"
#   - description: a short description of the API
#   - version: use the VERSION variable above
#
# Hint: app = FastAPI(title=..., description=..., version=...)
# YOUR CODE HERE


# ---------------------------------------------------------------------------
# TODO 2: Add CORS middleware
# ---------------------------------------------------------------------------
# Add CORSMiddleware to the app so browsers can call the API.
# Allow all origins for development. In production, restrict this.
#
# Hint:
#   app.add_middleware(
#       CORSMiddleware,
#       allow_origins=["*"],
#       allow_credentials=True,
#       allow_methods=["*"],
#       allow_headers=["*"],
#   )
# YOUR CODE HERE


# ---------------------------------------------------------------------------
# TODO 3: GET /health endpoint
# ---------------------------------------------------------------------------
# Create a GET endpoint at "/health" that returns a HealthResponse.
# It should report:
#   - status: "healthy"
#   - version: VERSION
#   - environment: ENVIRONMENT
#   - mock_mode: True (since we're using the mock agent)
#   - timestamp: current UTC time as ISO string
#
# Hint:
#   @app.get("/health", response_model=HealthResponse)
#   async def health():
#       return HealthResponse(...)
# YOUR CODE HERE


# ---------------------------------------------------------------------------
# TODO 4: POST /query endpoint (synchronous)
# ---------------------------------------------------------------------------
# Create a POST endpoint at "/query" that:
#   1. Accepts a QueryRequest body
#   2. Calls agent.query() with the request parameters
#   3. Converts the result into a QueryResponse
#   4. Handles errors gracefully (try/except -> HTTPException 500)
#
# The agent.query() method returns a dict with keys:
#   "answer", "filings", "risk", "processing_time_ms"
#
# You need to:
#   - Map filings (list of dicts) to FilingSummary objects
#   - Map risk (dict or None) to a RiskSummary object or None
#   - Set mock_mode=True
#
# Hint:
#   @app.post("/query", response_model=QueryResponse)
#   async def query(request: QueryRequest):
#       try:
#           result = agent.query(
#               query=request.query,
#               state=request.state,
#               include_risk=request.include_risk,
#               max_results=request.max_results,
#           )
#           filings = [FilingSummary(**f) for f in result["filings"]]
#           risk = RiskSummary(**result["risk"]) if result.get("risk") else None
#           return QueryResponse(
#               query=request.query,
#               answer=result["answer"],
#               filings=filings,
#               risk=risk,
#               processing_time_ms=result["processing_time_ms"],
#               mock_mode=True,
#           )
#       except Exception as e:
#           raise HTTPException(status_code=500, detail=str(e))
# YOUR CODE HERE


# ---------------------------------------------------------------------------
# TODO 5: POST /query/stream endpoint (Server-Sent Events)
# ---------------------------------------------------------------------------
# Create a POST endpoint at "/query/stream" that:
#   1. Accepts a QueryRequest body
#   2. Returns a StreamingResponse with media_type="text/event-stream"
#   3. Uses agent.query_stream() which yields SSE-formatted strings
#
# SSE (Server-Sent Events) lets the server push chunks to the client
# in real time. Each chunk is formatted as:
#   event: <type>\n
#   data: <json>\n\n
#
# The mock agent's query_stream() already yields properly formatted SSE.
#
# Hint:
#   @app.post("/query/stream")
#   async def query_stream(request: QueryRequest):
#       def generate():
#           yield from agent.query_stream(
#               query=request.query,
#               state=request.state,
#               include_risk=request.include_risk,
#               max_results=request.max_results,
#           )
#       return StreamingResponse(generate(), media_type="text/event-stream")
# YOUR CODE HERE


# ---------------------------------------------------------------------------
# Run with: python server.py
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=True)
