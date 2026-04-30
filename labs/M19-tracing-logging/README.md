# M19 Lab: Tracing & Logging

> A working agent without observability is a black box. **Traces** turn it into a glass box.

In this lab you build a complete tracing and structured-logging system from scratch — no external dependencies. You will instrument a UCC research agent so that every API call, tool execution, and error is recorded as a trace with nested spans, then render those traces in the terminal. You will also add a PII scrubber to keep sensitive data out of your logs.

## Prerequisites

- Python 3.10+ or Node.js 18+
- No API key required (uses a mock agent)
- No external tracing libraries (you build everything)

```bash
# Python — no extra packages needed (stdlib only)
python --version   # must be 3.10+

# Node.js — no extra packages needed
node --version     # must be 18+
```

## Exercises

| Step | Time | File | What You Build | Key Concept |
|------|------|------|---------------|-------------|
| 1 | 10 min | `trace_model.py` / `trace_model.js` | Trace & Span data model with context manager | Trace/span hierarchy, OpenTelemetry concepts |
| 2 | 10 min | `structured_logger.py` / `structured_logger.js` | JSON structured logger with PII scrubbing | Structured logs, log levels, PII redaction |
| 3 | 15 min | `instrumenter.py` / `instrumenter.js` | Agent instrumenter wrapping API + tool calls | Instrumentation, span attributes, error recording |
| 4 | 10 min | `trace_viewer.py` / `trace_viewer.js` | Terminal trace viewer + JSON export | Trace visualization, timing breakdown |
| 5 | 5 min | Run it all | End-to-end instrumented agent run | Putting it together |

## Step 1: Build the Trace Data Model (10 min)

**File:** `starter/trace_model.py` (or `.js`)

You will:
1. Implement a `Span` dataclass with: `span_id`, `trace_id`, `parent_span_id`, `name`, `start_time`, `end_time`, `duration_ms`, `attributes` (dict), `events` (list), `status` ("ok"/"error")
2. Implement a `Trace` class with: `trace_id`, `root_span`, flat `spans` list, `metadata` dict
3. Implement `SpanContext` — a context manager that auto-sets `start_time` on entry and `end_time`/`duration_ms` on exit
4. Run the self-test to create a sample trace with 3 nested spans

**Run it:**
```bash
python starter/trace_model.py
# or
node starter/trace_model.js
```

**Checkpoint:** You see a trace ID, 3 spans printed with names and durations. No errors.

## Step 2: Build the Structured Logger (10 min)

**File:** `starter/structured_logger.py` (or `.js`)

You will:
1. Implement `StructuredLogger` with `log(level, message, **kwargs)` producing JSON lines
2. Add convenience methods: `log_llm_call()`, `log_tool_call()`, `log_error()`
3. Implement `scrub_pii(data)` to redact SSNs, emails, and phone numbers
4. Run the self-test to see structured JSON log output with PII redacted

**Run it:**
```bash
python starter/structured_logger.py
# or
node starter/structured_logger.js
```

**Checkpoint:** Each log line is valid JSON. PII values (SSN, email, phone) are replaced with `[REDACTED]`.

## Step 3: Build the Agent Instrumenter (15 min)

**File:** `starter/instrumenter.py` (or `.js`)

You will:
1. Implement a mock agent that simulates: Claude call -> tool call -> Claude call -> response
2. Implement `InstrumentedAgent` that wraps the mock agent, creating spans for every operation
3. Each span captures: operation type, model name, token counts, duration, tool inputs/outputs
4. Errors are recorded as span events with stack traces
5. Run the self-test to execute the mock agent with full instrumentation

**Run it:**
```bash
python starter/instrumenter.py
# or
node starter/instrumenter.js
```

**Checkpoint:** You see structured log output for each agent step. The returned trace has 4 spans (1 root + 1 LLM + 1 tool + 1 LLM).

## Step 4: Build the Trace Viewer (10 min)

**File:** `starter/trace_viewer.py` (or `.js`)

You will:
1. Implement `render_trace(trace)` to display a tree view in the terminal:
   ```
   Trace abc123  |  Total: 150ms  |  3 spans
   ─────────────────────────────────────────
   [150ms] agent_request
   ├── [80ms] llm_call (claude-sonnet-4-6, 1200 tokens)  53.3%
   ├── [30ms] tool_execution (search_filings)  20.0%
   └── [40ms] llm_call (claude-sonnet-4-6, 800 tokens)  26.7%
   ```
2. Color-code spans by type (LLM = blue, tool = green, error = red)
3. Implement `render_trace_json(trace)` to export OpenTelemetry-compatible JSON
4. Run the self-test to render the mock trace from Step 3

**Run it:**
```bash
python starter/trace_viewer.py
# or
node starter/trace_viewer.js
```

**Checkpoint:** You see a colored tree view of spans with timing percentages. A JSON file is written.

## Step 5: Run the Instrumented Agent End-to-End (5 min)

Run the instrumenter, which exercises all four modules together:

```bash
python starter/instrumenter.py
# or
node starter/instrumenter.js
```

Compare your output against `expected_output/trace_output.txt`.

## Verification

After completing all exercises, run the solutions to see expected behavior:

```bash
# Python
python solution/trace_model.py
python solution/structured_logger.py
python solution/instrumenter.py
python solution/trace_viewer.py

# Node.js
node solution/trace_model.js
node solution/structured_logger.js
node solution/instrumenter.js
node solution/trace_viewer.js
```

## What You Built

By completing this lab, you have implemented:

1. **Trace/Span data model** — the same conceptual model used by OpenTelemetry, Jaeger, and Langfuse
2. **Structured logging** — JSON log lines that can be parsed by jq, Datadog, or any log aggregator
3. **PII scrubbing** — automatic redaction of SSNs, emails, and phone numbers before they hit logs
4. **Agent instrumentation** — wrapping every API call and tool execution in measured spans
5. **Trace visualization** — rendering parent-child span trees with timing breakdowns

This is the foundation for production observability in M20 (Cost Control) and M22B (Deployment).

## Next

- **M20**: Cost Control & Rate Limiting — track token usage and enforce budgets using the traces you built here
