# M19: Tracing & Logging

**Track**: 6 — Observability | **Position**: 19 of 30 | **Level**: Intermediate
**Prerequisites**: M05, M12
**Estimated Time**: 50-60 minutes
**Track Color**: var(--track-observability) / #22C55E
**SDK Tier**: 2 (dual-track). Lab ships `solution/` (manual logger that wraps each `client.messages.create()` call) AND `solution-sdk/` (tracing via `PreToolUse`/`PostToolUse` hooks plus iteration over the message stream from `query()`; demonstrates that hooks ARE the observability primitive in SDK-land). See `prompts/19-sdk-tier-policy.md`.

## Concepts
- Why observability matters for agents (animated "debugging blind" scenario)
- Agent traces: capturing every LLM call, tool call, and decision
- Spans: nesting and timing of sub-operations (animated trace waterfall)
- Structured logging: what to log, what NOT to log (PII considerations)
- Tools: LangSmith, Arize, Langfuse, OpenTelemetry comparison

## Hands-On Lab
Instrument the UCC research agent with Langfuse tracing. Capture: every Claude API call (input/output/tokens/latency), every tool execution (name/input/output/duration), full request trace. View traces in Langfuse dashboard.

## Quiz Focus (5 questions)
1. What is a trace? (the complete record of an agent handling one request)
2. What is a span? (a timed sub-operation within a trace)
3. Logging = tracing? (no — logging is text lines, tracing is structured with parent-child relationships)
4. Should you log the full Claude response? (careful — may contain PII from user input)
5. Traces cost nothing? (no — storage, processing, and retention have costs at scale)
