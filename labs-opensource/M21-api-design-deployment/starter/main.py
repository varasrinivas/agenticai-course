"""
M21 Lab: The FastAPI Service
=============================
Run: API_KEY=dev-secret-123 uvicorn main:app --port 8080
     (PowerShell: $env:API_KEY="dev-secret-123"; uvicorn main:app --port 8080)
Docs: http://localhost:8080/docs
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

# No key = no accidental open deployment — refuse to start (COMPLETE)
API_KEY = os.environ.get("API_KEY")
if not API_KEY:
    raise RuntimeError("API_KEY environment variable must be set")

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

app = FastAPI(title="Agent API (M21 Lab)", version="1.0.0")

# CORS — tighten allow_origins to your frontend domain in production (COMPLETE)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# ── TODO 1: API key auth dependency ──────────────────────────
async def verify_api_key(request: Request) -> str:
    """Extract and validate the Bearer token.

    TODO:
    1. auth = request.headers.get("Authorization", "")
    2. If not auth.startswith("Bearer "):
         raise HTTPException(status_code=401, detail="Missing Bearer token")
    3. token = auth.removeprefix("Bearer ").strip()
    4. If token != API_KEY:
         raise HTTPException(status_code=401, detail="Invalid API key")
    5. Return token
    """
    pass  # Remove this line when you add your code


# ── TODO 2: Global error handler ─────────────────────────────
@app.exception_handler(Exception)
async def global_error_handler(request: Request, exc: Exception):
    """Catch-all: never leak a raw stack trace to the client.

    TODO:
    1. request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    2. logger.exception(...) with the URL and request_id
    3. Return JSONResponse(status_code=500, content=ErrorResponse(
         error="internal_server_error",
         detail=str(exc) if os.environ.get("DEBUG") else None,  ← leak-guard
         request_id=request_id).model_dump())
    """
    pass  # Remove this line when you add your code


# ── TODO 3: Health check (NO auth — load balancers don't carry tokens) ──
@app.get("/health", tags=["ops"])
async def health():
    """TODO:
    1. import httpx; GET f"{OLLAMA_HOST}/api/tags" with timeout=3
       ollama_ok = (status_code == 200); any exception → ollama_ok = False
    2. Return {"status": "ok" if ollama_ok else "degraded",
               "ollama": ollama_ok, "version": app.version}
    """
    pass  # Remove this line when you add your code


# ── TODO 4: The agent route ──────────────────────────────────
@app.post(
    "/agent/run",
    response_model=AgentResponse,
    responses={422: {"model": ErrorResponse}},
    dependencies=[Depends(verify_api_key)],
    tags=["agent"],
)
async def run_agent_endpoint(body: AgentRequest, request: Request):
    """Synchronous agent invocation.

    TODO:
    1. start = time.perf_counter()
    2. result_data = await run_agent(query=body.query,
           session_id=body.session_id, max_iterations=body.max_iterations,
           ollama_host=OLLAMA_HOST)
    3. latency_ms = int((time.perf_counter() - start) * 1000)
    4. Return AgentResponse(latency_ms=latency_ms, **result_data)
    NOTE: validation already happened — FastAPI rejected malformed bodies
    with 422 before this function was ever called. That's the point of
    typed contracts.
    """
    pass  # Remove this line when you add your code
