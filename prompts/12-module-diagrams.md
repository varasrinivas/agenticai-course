# Module Diagram Requirements

Every module MUST have embedded SVG diagrams for its core concepts. Diagrams are NOT optional decoration — they are primary teaching tools. A student should be able to understand the concept from the diagram ALONE without reading the text.

## Diagram Design Rules

1. **SVG only** — embedded inline in the HTML, not external files
2. **Dark theme** — background transparent, strokes and fills use CSS variables from the design system
3. **Animated where useful** — CSS transitions for flow diagrams, static for reference diagrams
4. **Labeled** — every box, arrow, and connection has a text label
5. **Color-coded** — use track colors to distinguish components (tools = purple, memory = cyan, guardrails = red, etc.)
6. **Maximum 600px wide** — fits mobile without horizontal scroll
7. **prefers-reduced-motion** — show all elements visible in static layout
8. **Alt text** — every SVG has aria-label describing the diagram

## Required Diagrams Per Module

### M01: LLM Mental Model
1. **How an LLM generates text** — input tokens → transformer layers → probability distribution → output token → repeat (left-to-right flow)
2. **Context window visualization** — rectangle showing system prompt + conversation history + user message + space for response, with token counts

### M02: Tokens
1. **Tokenization example** — sentence splits into colored token blocks, showing word tokens vs subword tokens vs single-char tokens
2. **Token cost calculator** — visual showing input tokens + output tokens = total cost at different model prices

### M03: Prompts
1. **Message role flow** — system (top, persistent) → user → assistant → user → assistant stacked conversation
2. **Prompting patterns comparison** — three columns: zero-shot (just question), few-shot (examples + question), chain-of-thought (examples + reasoning + question)

### M04: Structured Output
1. **Tool use flow** — user message → Claude → tool_use response → YOUR CODE executes → tool_result → Claude → final response
2. **Schema validation pipeline** — raw LLM output → Pydantic/Zod validator → valid structured data OR retry

### M05: Function Calling
1. **The tool use loop** — circular flow: Send message → Check stop_reason → tool_use? Execute tool and loop back : end_turn? Return response
2. **Tool definition anatomy** — annotated JSON Schema showing name, description, input_schema, properties, required

### M06: Multi-Tool
1. **Parallel vs sequential tools** — side by side: parallel (3 tools called simultaneously) vs sequential (tool A output feeds tool B feeds tool C)
2. **Tool selection degradation** — bar chart showing accuracy vs number of tools (high at 3-5, drops at 8+)

### M07: MCP
1. **MCP architecture** — Client (Claude Desktop/Code) ↔ MCP Protocol (JSON-RPC) ↔ Server (your code) ↔ Resources/Tools/Prompts
2. **N times M vs N plus M** — before MCP (grid of connections) vs after MCP (hub and spoke)
3. **Transport comparison** — stdio (local, subprocess) vs HTTP+SSE (remote, network)

### M08: Conversation Management
1. **Stateless reality** — API call 1 (full context) → response. API call 2 (full context AGAIN) → response. No arrow between calls.
2. **Three memory strategies** — full history (all messages) vs sliding window (last N) vs summarize (compress old into summary)
3. **Token budget allocation** — stacked bar: system prompt (fixed) + history (variable) + user message + response headroom

### M09: RAG
1. **RAG pipeline end-to-end** — Documents → Chunk → Embed → Store in vector DB → User question → Embed question → Search → Top K chunks → Claude + chunks → Response with citations
2. **Embedding space** — 2D scatter plot showing document chunks as dots, query as a star, nearest neighbors highlighted with distance lines
3. **Chunking comparison** — same document shown chunked 3 ways: fixed-size (rigid cuts), semantic (paragraph boundaries), recursive (hierarchical)

### M10: Advanced RAG
1. **Naive vs advanced RAG** — two parallel pipelines: naive (embed → search → generate) vs advanced (embed → hybrid search → re-rank → compress → generate)
2. **HyDE flow** — user question → generate hypothetical answer → embed hypothetical → search → real results

### M11: Multi-Layer Memory
1. **Three-tier brain diagram** — concentric layers: inner (working memory/scratchpad), middle (episodic/vector DB of past interactions), outer (procedural/learned patterns)
2. **Memory activation timeline** — horizontal timeline of a request showing when each tier activates

### M12: ReAct + Design Patterns
1. **8 Agent Design Patterns catalog** — grid of 8 cards each with icon and one-line description
2. **Pattern decision tree** — flowchart: needs tools? → one tool? → known steps? → many inputs? → routing to the right pattern
3. **ReAct loop** — circular: Think (thought bubble) → Act (tool call) → Observe (result) → back to Think, with exit arrow on end_turn
4. **Combining patterns** — show CAPSTONE-4 as Router → Pipeline → HITL connected blocks

### M13: Planning
1. **Task decomposition tree** — complex request at top, decomposed into 4 sub-tasks, each with tool assignments
2. **DAG execution** — directed graph showing parallel and sequential paths with timing annotations

### M14: Multi-Agent
1. **Three architecture patterns** — supervisor/worker (star topology), peer-to-peer (mesh), pipeline (assembly line)
2. **Context isolation** — coordinator has its context window, each subagent has its OWN separate context window, explicit data flows between them

### M15: Code Interpreter
1. **Sandbox architecture** — host machine → Docker container → sandboxed Python → result extraction → back to agent
2. **Security boundary** — what the sandbox CAN access (CPU, limited memory) vs CANNOT (host filesystem, network, other containers)

### M15B: Build Complete Agent
1. **System architecture** — coordinator → filing search subagent → risk analysis subagent → tools → mock data → response assembly
2. **Single agent vs coordinator comparison** — single (one agent, all tools) vs coordinator (hub with specialist spokes)

### M16: Input Guardrails
1. **Guardrail pipeline** — raw input → PII detector → injection filter → schema validator → sanitized input (gates that pass/block)
2. **Prompt injection anatomy** — legitimate prompt structure vs injected malicious instruction highlighted in red

### M17: Output Guardrails + HITL
1. **Confidence routing** — agent output → confidence check → high (>90%): auto-approve → medium (70-90%): HITL queue → low (<70%): auto-deny
2. **Circuit breaker state machine** — CLOSED (normal) → failures accumulate → OPEN (blocked) → cooldown timer → HALF-OPEN (test) → success? back to CLOSED

### M18: Evaluation
1. **Eval pipeline** — test dataset → run agent → collect outputs → score (auto + human) → metrics dashboard → compare versions
2. **Aggregate vs per-type accuracy** — overall 95% bar, but broken down: Type A 99%, Type B 98%, Type C 72% (masked failure)

### M19: Tracing
1. **Trace waterfall** — horizontal nested bars: total request → coordinator (0.1s) → agent 1 (0.3s) → tool call (0.05s) → agent 2 (1.8s) → RAG search (0.4s)
2. **What to log vs not log** — two columns: YES (timestamps, tool names, token counts, latency) vs NO (PII, API keys, full user data)

### M20: Monitoring
1. **Dashboard layout** — 4-panel dashboard mockup: request rate, p95 latency, error rate, cost per request
2. **Drift detection** — line chart showing agent accuracy over time, gradual decline highlighted with alert threshold

### M21: API Design
1. **Streaming flow** — client → request → server → SSE stream: chunk1, chunk2, tool_use_progress, chunk3, done
2. **Deployment pipeline** — code → Dockerfile → build → push to registry → deploy to Cloud Run/Lambda → user hits URL

### M22: Cost Optimization
1. **Cost breakdown waterfall** — stacked bar: system prompt tokens + history tokens + tool call tokens + response tokens = total, with cache savings overlay
2. **Model routing decision** — request → complexity classifier → simple: Haiku ($) → moderate: Sonnet ($$) → complex: Opus ($$$)

### M22B: Deploy Agent
1. **3-tier deployment comparison** — three columns: Local Docker, GCP Cloud Run, AWS Lambda with icons and key differences
2. **Docker multi-stage build** — stage 1 (install deps, large) → stage 2 (copy only needed files, small) → final image

### M25: Claude Code
1. **CLAUDE.md hierarchy** — root CLAUDE.md → project CLAUDE.md → .claude/commands/ → .claude/skills/ showing inheritance
2. **Slash command execution** — user types /command → Claude reads command.md → reads referenced prompt files → executes

### M26: Hooks + Agent SDK
1. **Hook lifecycle** — PreToolUse → tool executes → PostToolUse → check result → continue or block
2. **Agent SDK loop** — create agent → send message → agent runs (tools + thinking) → stop_reason check → return or continue

### M27: Cert Exam Prep
1. **Exam domain coverage** — pie chart: Domain 1 (25%), Domain 2 (20%), Domain 3 (20%), Domain 4 (20%), Domain 5 (15%)
2. **Anti-pattern identification flow** — code snippet → red flag indicator → anti-pattern name → correct pattern
