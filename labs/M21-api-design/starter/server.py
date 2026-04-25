"""
M21: UCC Agent API Server — Starter
FastAPI application wrapping the UCC research agent.

Your task: Complete the 6 TODOs below to build a production API server.
Run with:  python server.py
Test with: curl http://localhost:8000/health
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
# TODO 1: Create FastAPI app with metadata
#
# Create a FastAPI instance with:
#   - title: "UCC Research Agent API"
#   - version: "1.0.0"
#   - description: a short description of what the API does
#
# Example:
#   app = FastAPI(title="...", version="...", description="...")
# ---------------------------------------------------------------------------
# app = FastAPI(...)  # TODO: uncomment and fill in


# ---------------------------------------------------------------------------
# TODO 2: Add CORS middleware
#
# Use app.add_middleware(CORSMiddleware, ...) with:
#   - allow_origins=["*"]  (allow all origins — DEV ONLY)
#   - allow_credentials=True
#   - allow_methods=["*"]
#   - allow_headers=["*"]
#
# SECURITY NOTE: In production, replace ["*"] with your actual frontend
# domains, e.g. ["https://app.yourcompany.com"]. Allowing all origins
# means any website can call your API.
# ---------------------------------------------------------------------------
# TODO: Add CORS middleware here


# ---------------------------------------------------------------------------
# TODO 3: GET /health endpoint
#
# Create a GET endpoint at "/health" that returns a HealthResponse with:
#   - status: "ok"
#   - version: app.version (from the FastAPI app metadata)
#   - uptime_seconds: seconds since START_TIME (use time.time() - START_TIME)
#   - model: "claude-sonnet-4-20250514"
#
# Hint: Use @app.get("/health", response_model=HealthResponse)
# ---------------------------------------------------------------------------
# TODO: Implement health endpoint


# ---------------------------------------------------------------------------
# TODO 4: POST /query endpoint
#
# Create a POST endpoint at "/query" that:
#   1. Accepts a QueryRequest body
#   2. Validates the query is not empty (raise HTTPException 400 if it is)
#   3. Generates a request_id using str(uuid.uuid4())
#   4. Records start time
#   5. Calls mock_query(request.query)
#   6. Calculates duration_ms
#   7. Returns a QueryResponse with all fields populated
#   8. Wraps everything in try/except — on error, return JSONResponse
#      with status 500 and an ErrorResponse body
#
# Hint: Use @app.post("/query", response_model=QueryResponse)
# ---------------------------------------------------------------------------
# TODO: Implement query endpoint


# ---------------------------------------------------------------------------
# TODO 5: POST /query/stream endpoint
#
# Create a POST endpoint at "/query/stream" that:
#   1. Accepts a QueryRequest body
#   2. Validates the query is not empty
#   3. Generates a request_id
#   4. Defines an async generator function that:
#      a. Iterates over mock_stream(request.query)
#      b. For each chunk, yields an SSE line:
#         f"data: {StreamChunk(chunk=..., done=False, request_id=...).model_dump_json()}\n\n"
#      c. After the loop, yields a final SSE line with done=True and empty chunk
#   5. Returns StreamingResponse(generator(), media_type="text/event-stream")
#
# SSE format reminder:
#   Each event is: "data: {json}\n\n" (note the double newline)
#   The client reads these one at a time as they arrive
# ---------------------------------------------------------------------------
# TODO: Implement streaming endpoint


# ---------------------------------------------------------------------------
# TODO 6: Global exception handler
#
# Add an exception handler for Exception (catch-all) that:
#   1. Generates a request_id
#   2. Logs the error (print or use logging)
#   3. Returns a JSONResponse with status_code=500 and an ErrorResponse body
#
# Hint: Use @app.exception_handler(Exception)
#       async def handle_exception(request: Request, exc: Exception):
# ---------------------------------------------------------------------------
# TODO: Implement exception handler


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
