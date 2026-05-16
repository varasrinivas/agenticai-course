# Capstone 5 — Production Agent Spec (Domain C: UCC Public Records)

> Canonical `agent-spec.md` for the Capstone-5 production agent. Drives `/generate-from-spec` to produce the full project. The hand-built `solution/` is the reference; this spec is what the student iterates on.

## Overview
A production-grade UCC filing risk agent that combines: multi-agent orchestration (research/analysis/communication), persistent memory across sessions, observability (tracing + metrics), guardrails (PII + prompt injection), evaluation harness, and deployment to Docker / Cloud Run / Lambda.

This is the capstone — the agent the student has been building toward since M01.

## Agent Configuration
- Model (coordinator): `claude-sonnet-4-6`
- Model (specialist subagents): `claude-haiku-4-5-20251001`
- Framework: `claude-agent-sdk` (Python)
- Max turns per request: 12
- Sessions: persistent across invocations (SQLite-backed)
- Streaming: yes — surface intermediate events to the API caller via SSE

## System Prompt (coordinator)
You are the production coordinator for a UCC credit-risk research system used by lending analysts. For every request:
1. Decide which specialist subagents to invoke: filing-research, risk-analysis, communication.
2. Delegate with explicit, focused context — subagents do not see the conversation.
3. Synthesize a final response that cites filing numbers, includes the risk score, and ends with a clear recommendation.
4. If any specialist reports a data gap or a guardrail trip, surface it transparently. Never fabricate.

## Tools (exposed via `ucc_prod` MCP server)

### search_filings
- Description: Search UCC filings by debtor name, state, or date range. Backed by a real DuckDB instance loaded from the mock dataset.
- Parameters: `debtor_name` (string, optional), `state` (string, optional), `since` (ISO date, optional)
- Returns: filing summaries

### get_filing_details
- Description: Full filing record by filing number.
- Parameters: `filing_number` (string, required)

### calculate_risk_score
- Description: Aggregate risk profile for a debtor.
- Parameters: `debtor_name` (string, required)
- Returns: score, level, factors, recommendation

### draft_credit_memo
- Description: Generate a credit memo paragraph from a risk profile.
- Parameters: `risk_profile` (object, required), `tone` (string: "internal"|"external", default "internal")

### lookup_memory
- Description: Retrieve prior research on a debtor from the persistent memory layer.
- Parameters: `debtor_name` (string, required)
- Returns: prior risk scores, prior reports, last_assessed_at

### store_memory
- Description: Persist a research result for future sessions.
- Parameters: `debtor_name` (string, required), `risk_score` (float), `summary` (string)

## Subagents (declared as `.claude/agents/<name>.md`)

### filing-research
- Tools: `search_filings`, `get_filing_details`, `lookup_memory`
- Model: `claude-haiku-4-5-20251001`
- Behavior: Always check `lookup_memory` first; if the debtor was researched in the last 30 days and nothing's changed, return the cached result.

### risk-analysis
- Tools: `calculate_risk_score`, `search_filings`
- Model: `claude-haiku-4-5-20251001`
- Behavior: Compute score; if score is HIGH, return top 5 contributing factors; if MEDIUM/LOW, return top 3.

### communication
- Tools: `draft_credit_memo`, `store_memory`
- Model: `claude-sonnet-4-6` (writing quality matters here)
- Behavior: Draft the credit memo; store the result via `store_memory` so the next session can reuse it.

## Hooks

### PreToolUse — PII / injection guardrails
- Matcher: `*`
- Implementation: `hooks/guardrails.py` blocks prompt injection patterns; redacts SSN/credit-card/email before tool dispatch

### PreToolUse — rate limit
- Matcher: `mcp__ucc_prod__*`
- Implementation: Token-bucket per debtor name; deny with `PermissionResultDeny` when exceeded

### PostToolUse — tracing + metrics
- Matcher: `*`
- Implementation: Emit OpenTelemetry span (`tool_name`, duration, input_size, output_size) and Prometheus counter (`agent_tool_calls_total{tool_name}`)

### PostToolUse — audit log
- Matcher: `*`
- Implementation: Append to DuckDB `audit_events` table — required for compliance review

## Sessions
- SQLite-backed `SessionManager` with persistent transcript across process restarts
- `SessionManager.fork(session_id)` for what-if branches that don't pollute the main session
- Session TTL: 24 hours; expired sessions are archived, not deleted

## API Wrapper (FastAPI)
- `POST /query` — synchronous; returns final answer
- `POST /query/stream` — SSE stream of `AssistantMessage` content blocks plus tool events
- `POST /chat` — multi-turn with `session_id` cookie
- `GET /health` — liveness; checks SDK init + DB connection
- `GET /metrics` — Prometheus scrape endpoint
- Auth: API key in `X-API-Key` header
- Rate limit: 30 RPM per key

## Memory
- DuckDB at `memory/ucc_research.duckdb`
- Tables: `research_results`, `audit_events`, `sessions`
- `lookup_memory` / `store_memory` tools wrap the DuckDB calls

## Deployment

### Tier 1 — Local
- `docker-compose up` brings up: agent (FastAPI), DuckDB volume, Prometheus, Grafana
- Image installs `claude-agent-sdk` and the project

### Tier 2 — GCP Cloud Run
- Same image; Secret Manager for `ANTHROPIC_API_KEY`
- Cloud SQL for memory (Postgres) instead of DuckDB
- Cloud Trace receives OTel spans

### Tier 3 — AWS Lambda
- Lambda layer with `claude-agent-sdk` and dependencies
- DynamoDB for memory
- API Gateway in front; CloudWatch for traces/metrics
- Note: streaming requires Lambda response streaming + API Gateway HTTP API (REST does not support SSE)

## Tests (pytest)
- `test_tools.py` — every `@tool` returns the canonical content-array shape
- `test_subagents.py` — each subagent reaches its allowed tools and respects context isolation
- `test_hooks.py` — guardrails block injection; rate limit denies after threshold; PostToolUse appends audit row
- `test_sessions.py` — persistence across simulated restart; `fork()` produces independent transcripts
- `test_eval.py` — runs all 25 evaluation scenarios, asserts ≥90% pass rate
- `test_api.py` — `/query` returns 200, `/query/stream` yields ≥3 events, `/health` returns "ok"

## Evaluation Dataset (25 scenarios in `evaluation/scenarios.json`)
Seven categories: lookup, risk-comparison, memory-recall, what-if, edge-case-empty-result, edge-case-injection, edge-case-rate-limit. Each scenario has expected response markers (specific filing numbers cited, expected risk level, etc.).

## File Structure
```
generated/
├── CLAUDE.md
├── .claude/
│   ├── agents/
│   │   ├── filing-research.md
│   │   ├── risk-analysis.md
│   │   └── communication.md
│   ├── commands/
│   │   ├── run-agent.md
│   │   ├── eval.md
│   │   └── deploy.md
│   └── settings.json
├── coordinator.py
├── tools.py
├── hooks/
│   ├── guardrails.py
│   ├── rate_limit.py
│   ├── tracing.py
│   └── audit.py
├── memory/
│   ├── schema.sql
│   ├── ucc_research.duckdb (created at first run)
│   └── memory_layer.py
├── session_manager.py
├── api/
│   ├── server.py
│   └── auth.py
├── evaluation/
│   ├── scenarios.json
│   └── runner.py
├── observability/
│   ├── otel_setup.py
│   └── prometheus_metrics.py
├── deploy/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── cloud-run/
│   └── lambda/
├── tests/
└── requirements.txt
```

## Acceptance Criteria
- All Python files import from `claude_agent_sdk` only — no `client.messages.create()` calls anywhere
- `pytest` passes 100%
- `python evaluation/runner.py` returns ≥90% pass on the 25-scenario set
- `docker-compose up` produces a working `/query` endpoint with a Grafana dashboard showing live tool-call metrics
- Asking the agent twice for the same debtor uses memory the second time (verifiable via the audit log)
- Sending a prompt-injection input returns a denial without dispatching any tool

## How students use this spec
1. Read it end-to-end alongside the existing `solution/` — understand which sections of the spec map to which directories.
2. Run `/generate-from-spec spec/agent-spec.md` from the capstone root. Output goes to `generated/`.
3. Diff `generated/` against `solution/` — the differences ARE the discussion (architectural choices the spec did not lock down).
4. Iterate: add a new subagent to the spec (e.g., `lapse-monitor`), regenerate, see targeted edits.
