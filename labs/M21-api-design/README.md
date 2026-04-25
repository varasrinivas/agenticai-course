# M21 Lab: API Design & Deployment

> Track 7 — Production Deployment | Prerequisites: M12, M16-M17, M19 | Time: 60-75 min

You built a UCC research agent. You added guardrails, evaluation, and tracing. Now it is time to **ship it**. This lab wraps your agent in a production FastAPI application with synchronous and streaming endpoints, health monitoring, structured error handling, and Docker packaging.

**Estimated time: 60-75 minutes** | **70% hands-on lab, 30% concept**

## What You'll Build

A production-ready API server for the UCC research agent with:
- **FastAPI application** with 3 endpoints: `POST /query`, `POST /query/stream`, `GET /health`
- **Pydantic request/response models** for type-safe validation
- **CORS middleware** for cross-origin access
- **Error handling middleware** with structured error responses
- **SSE streaming** for real-time agent output
- **Docker packaging** following security best practices

## Prerequisites

- Python 3.10+ or Node.js 18+
- No API key needed — this lab uses a mock agent
- Install dependencies:
  ```bash
  cd starter
  pip install -r requirements_api.txt
  ```

## Project Structure

```
M21-api-design/
├── README.md
├── starter/
│   ├── models.py            # TODO — Pydantic request/response models
│   ├── mock_agent.py        # Complete — mock UCC agent (no API key needed)
│   ├── server.py            # TODO — FastAPI server with 3 endpoints
│   ├── Dockerfile           # TODO — Docker packaging
│   ├── requirements_api.txt # Complete — Python dependencies
│   └── test_api.sh          # Complete — curl test script
├── solution/
│   ├── models.py            # Complete Python implementation
│   ├── mock_agent.py        # Same as starter (complete)
│   ├── server.py            # Complete Python implementation
│   ├── Dockerfile           # Complete Dockerfile
│   ├── requirements_api.txt # Same as starter (complete)
│   ├── test_api.sh          # Same as starter (complete)
│   ├── server.js            # Node.js/Express implementation
│   ├── models.js            # Zod validation (Node.js)
│   ├── mock_agent.js        # Node.js mock agent
│   └── package.json         # Node.js dependencies
└── expected_output/
    └── api_output.txt       # Sample curl test results
```

## Lab Steps

### Step 1: Build Request/Response Models (10 min)

**File:** `starter/models.py`

Define the data contracts for your API using Pydantic:
1. `QueryRequest` — what the client sends (query, optional session_id, stream flag)
2. `QueryResponse` — what the server returns (answer, sources, metrics)
3. `HealthResponse` — system status (uptime, version, model)
4. `StreamChunk` — one piece of a streaming response
5. `ErrorResponse` — structured error with request tracing

```bash
cd starter
python models.py
```

**Checkpoint:** Self-test passes — all 5 models can be instantiated and serialized to JSON.

### Step 2: Build the Mock Agent (5 min)

**File:** `starter/mock_agent.py`

This file is **already complete**. Review it to understand the agent interface:
- `mock_query(query)` — returns a dict with answer, sources, tokens_used
- `mock_stream(query)` — yields string chunks with simulated latency

```bash
python mock_agent.py
```

**Checkpoint:** You see a mock response and streaming chunks printed to the console.

### Step 3: Build the FastAPI Server (20 min)

**File:** `starter/server.py`

Build the core server with two endpoints and middleware:
1. Create the `FastAPI` app with metadata (title, version, description)
2. Add CORS middleware — allow all origins for development
3. Implement `GET /health` — return uptime, version, model name
4. Implement `POST /query` — accept `QueryRequest`, call `mock_query`, return `QueryResponse`
5. Include `request_id` (UUID4) and `duration_ms` in every response

```bash
python server.py
```

Then in a separate terminal:
```bash
curl http://localhost:8000/health | python -m json.tool
```

**Checkpoint:** Health endpoint returns valid JSON with status "ok" and uptime in seconds.

### Step 4: Add the Streaming Endpoint (15 min)

**File:** `starter/server.py` (continue editing)

Add SSE (Server-Sent Events) streaming:
1. Implement `POST /query/stream`
2. Return `StreamingResponse` with `media_type="text/event-stream"`
3. Each chunk follows SSE format: `data: {"chunk": "...", "done": false, "request_id": "..."}\n\n`
4. Final chunk has `done: true`

```bash
curl -N -X POST http://localhost:8000/query/stream \
  -H "Content-Type: application/json" \
  -d '{"query": "Find UCC filings for Acme Corp"}'
```

**Checkpoint:** You see chunks arriving one at a time in the terminal.

### Step 5: Add Error Handling (5 min)

**File:** `starter/server.py` (continue editing)

Add a global exception handler:
1. Catch all unhandled exceptions
2. Return `ErrorResponse` with HTTP 500
3. Include `request_id` for tracing

Test with an empty query:
```bash
curl -s -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": ""}' | python -m json.tool
```

**Checkpoint:** Empty query returns a 400 error with a structured JSON error body.

### Step 6: Test with curl (10 min)

**File:** `starter/test_api.sh`

Run the complete test suite:
```bash
# Start server in one terminal
python server.py

# Run tests in another terminal
bash test_api.sh
```

All 4 tests should pass: health check, sync query, streaming query, error handling.

### Step 7: Package in Docker (10 min)

**File:** `starter/Dockerfile`

Build a production Docker image:
1. Use `python:3.11-slim` as the base
2. Copy requirements first (layer caching)
3. Create a non-root user
4. Expose port 8000

```bash
docker build -t ucc-agent-api .
docker run -p 8000:8000 ucc-agent-api
```

Then re-run your curl tests against the containerized server.

**Checkpoint:** All curl tests pass against the Docker container.

## Verification

Run the solutions to see expected behavior:

```bash
# Python
cd solution
pip install -r requirements_api.txt
python server.py
# In another terminal: bash test_api.sh

# Node.js
cd solution
npm install
node server.js
# In another terminal: bash test_api.sh
```

Compare your output against `expected_output/api_output.txt`.

## What You Built

1. **Pydantic models** for type-safe request/response validation
2. **FastAPI server** with health, sync query, and streaming endpoints
3. **CORS middleware** for cross-origin browser access
4. **SSE streaming** for real-time agent output
5. **Error handling** with structured responses and request tracing
6. **Docker packaging** with security best practices

## Key Takeaways

- **Pydantic models are your API contract** — they auto-generate docs, validate inputs, and serialize outputs
- **Health endpoints are non-negotiable** — load balancers, orchestrators, and monitoring systems all need them
- **SSE is simpler than WebSockets** for one-directional streaming (agent to client)
- **Request IDs enable tracing** — every response should include one for debugging
- **Non-root Docker users** are a baseline security requirement, not an optimization
- **CORS must be locked down in production** — `allow_origins=["*"]` is for development only

## Next

- **M22**: Scaling & Optimization — horizontal scaling and rate limiting
- **M22B**: Build Lab — deploy to Docker, GCP Cloud Run, and AWS Lambda
