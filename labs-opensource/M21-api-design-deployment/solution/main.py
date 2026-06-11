"""
M21 Lab: The FastAPI Service — SOLUTION
========================================
Run: API_KEY=dev-secret-123 uvicorn main:app --port 8080
"""

import logging
import os
import time
import uuid

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from agent import run_agent
from models import AgentRequest, AgentResponse, ErrorResponse

logger = logging.getLogger(__name__)

# No key = no accidental open deployment — refuse to start
API_KEY = os.environ.get("API_KEY")
if not API_KEY:
    raise RuntimeError("API_KEY environment variable must be set")

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

app = FastAPI(title="Agent API (M21 Lab)", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to your frontend domain in production
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


async def verify_api_key(request: Request) -> str:
    """Dependency: extract and validate the Bearer token."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    token = auth.removeprefix("Bearer ").strip()
    if token != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return token


@app.exception_handler(Exception)
async def global_error_handler(request: Request, exc: Exception):
    """Catch-all: never leak a raw stack trace to the client."""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    logger.exception("Unhandled error on %s (req=%s)", request.url, request_id)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="internal_server_error",
            detail=str(exc) if os.environ.get("DEBUG") else None,  # leak-guard
            request_id=request_id,
        ).model_dump(),
    )


@app.get("/health", tags=["ops"])
async def health():
    """Load balancer probe — NO auth; LBs don't carry tokens."""
    import httpx
    try:
        r = httpx.get(f"{OLLAMA_HOST}/api/tags", timeout=3)
        ollama_ok = r.status_code == 200
    except Exception:
        ollama_ok = False
    return {
        "status": "ok" if ollama_ok else "degraded",
        "ollama": ollama_ok,
        "version": app.version,
    }


@app.post(
    "/agent/run",
    response_model=AgentResponse,
    responses={422: {"model": ErrorResponse}},
    dependencies=[Depends(verify_api_key)],
    tags=["agent"],
)
async def run_agent_endpoint(body: AgentRequest, request: Request):
    """Synchronous agent invocation. Validation happened before we got here."""
    start = time.perf_counter()
    result_data = await run_agent(
        query=body.query,
        session_id=body.session_id,
        max_iterations=body.max_iterations,
        ollama_host=OLLAMA_HOST,
    )
    latency_ms = int((time.perf_counter() - start) * 1000)
    return AgentResponse(latency_ms=latency_ms, **result_data)
