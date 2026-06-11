# M19 Lab: Tracing & Logging

> When an agent misbehaves at 2am, your trace file is the only witness. You'll build a zero-dependency JSONL tracer covering the four event categories — tool calls, LLM turns, loop iterations, errors — instrument an agent with it, and read the result in a CLI trace viewer.

## Prerequisites

- M05 complete (the agent you'll instrument is the M05 weather/calc agent)

## Files

| File | Status | What It Is |
|------|--------|------------|
| `tracer.py` | **TODOs** | `TraceEvent` schema (complete) + `TraceRecorder` (you build) |
| `traced_agent.py` | **TODOs** | The M05 agent with emit-points for you to fill |
| `trace_viewer.py` / `trace_viewer.mjs` | Complete | CLI pretty-printer with slow-step detection |

> Python is the full lab here. The Node.js viewer (`trace_viewer.mjs`) reads the same JSONL, so a JS agent instrumented with the identical schema plugs straight in — the course HTML has the TypeScript `TraceRecorder` mirror.

## Step 1: TraceRecorder

`TraceEvent` (provided) is one dataclass for all four categories — one JSON schema, one destination, one filter. You implement:
- `emit(event)`: validate `category` against `VALID_CATEGORIES` (raise on unknown), append `event.to_json() + "\n"` to the JSONL file
- The four convenience builders: `tool_call()` (truncate output to 2,048 chars!), `llm_turn()`, `loop_iter()`, `error()` (keep only the **last 3 stack frames** — full stacks bloat trace files)

## Step 2: Instrument the Agent

`traced_agent.py` is the M05 loop with `# TODO: emit` markers at the four instrumentation points:
1. After each model response → `recorder.llm_turn(model, prompt_tokens, completion_tokens, finish_reason, latency_ms, turn_index)`
2. Around each tool execution → `recorder.tool_call(name, args, output, latency_ms, ok, error)`
3. At the end of each loop iteration → `recorder.loop_iter(...)`
4. In the exception handler → `recorder.error(exc)`

**The discipline being taught:** time everything (`time.perf_counter()` around each call) and never let tracing break the agent — emit failures should be swallowed, not raised.

## Step 3: Read the Trace

```bash
python starter/traced_agent.py            # writes traces/trace_<runid>.jsonl
python starter/trace_viewer.py traces/trace_*.jsonl --slow-threshold 1000
```

The viewer prints a colored call tree (LLM turns, tool calls with ✓/✗, errors) plus a category breakdown table and a slow-steps report. On local CPU, *every* LLM turn will exceed a 1000ms threshold — that's the point: you can now SEE where the time goes.

## Production Alternatives (course HTML covers these)

This lab's tracer is the zero-dependency teaching version. Production options: `structlog`/`pino` for structured logs, LangSmith's `@traceable` (works with Ollama), OpenTelemetry + Jaeger for distributed traces. The JSONL schema you built maps 1:1 onto OTel spans — nothing is wasted.

## Stretch Goals

- Add a `run_start`/`run_end` event pair and total-runtime computation in the viewer
- Compute cost-per-run from the `llm_turn` token counts (M17's prices)
- Load the JSONL into pandas and find your p95 tool latency
