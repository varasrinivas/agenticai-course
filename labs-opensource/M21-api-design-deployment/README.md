# M21 Lab: API Design & Deployment

> An agent nobody can call is a demo. You'll wrap an agent as a FastAPI service with typed contracts, Bearer-token auth, a health check that probes Ollama, and a global error envelope — then hit it with a test client.

## Prerequisites

- M05 complete; `pip install fastapi uvicorn httpx`

## Files

| File | Status | What It Is |
|------|--------|------------|
| `models.py` | Complete | Pydantic request/response/error contracts |
| `agent.py` | Complete | A minimal agent (M05 loop) the API wraps |
| `main.py` | **TODOs** | The FastAPI app — you build auth, health, the route |
| `test_client.py` | Complete | httpx test script (valid, unauthorized, malformed requests) |

The Node.js mirror (Express + Zod, identical structure) ships complete in `solution/app.js` as a reference — the design transfers 1:1.

## What You Implement (in `main.py`)

1. **`verify_api_key(request)`** — FastAPI dependency: require `Authorization: Bearer <API_KEY>`; 401 on missing/wrong token. The key comes from the `API_KEY` env var, and the app **refuses to start without it** (no key = no accidental open deployment).
2. **`global_error_handler`** — catch-all exception handler returning the `ErrorResponse` envelope with a request ID; include exception detail ONLY when `DEBUG` is set (stack traces are information leaks).
3. **`/health`** — probe `{OLLAMA_HOST}/api/tags` with a 3s timeout; return `ok` / `degraded` + the ollama flag. **Health checks must never require auth** (load balancers don't carry tokens).
4. **`POST /agent/run`** — validate via the `AgentRequest` model (FastAPI does it from the type hint), call `run_agent(...)`, measure wall-clock latency, return `AgentResponse`.

## Run It

```bash
# Terminal 1 — start the service
cd starter
API_KEY=dev-secret-123 uvicorn main:app --port 8080
# Windows PowerShell: $env:API_KEY="dev-secret-123"; uvicorn main:app --port 8080

# Terminal 2 — run the test client
API_KEY=dev-secret-123 python test_client.py
```

The test client sends: a valid request (expect 200 + JSON contract), no token (expect 401), wrong token (401), empty query (422 from Pydantic — your code never even ran), and hits `/health`.

Also open http://localhost:8080/docs — FastAPI generated interactive API docs from your Pydantic models for free.

## Deployment Stretch Goals (course HTML has full configs)

- **Docker**: multi-stage Dockerfile + docker-compose with an Ollama sidecar (`OLLAMA_HOST=http://ollama:11434` — service name, not localhost!)
- **SSE streaming**: add `/agent/stream` using `StreamingResponse` and `stream=True` on the Ollama call
- **Async jobs**: `/agent/jobs` + `/agent/jobs/{id}` for long-running queries (in-process asyncio queue)
- Add the M16 rate limiter as a FastAPI dependency
