# Building AI Agents with Claude — Revision Summary

A concept-only summary of the full 30-module course. No code. Designed for a few hours of focused revision before the Claude Certified Architect — Foundations exam (or before re-reading the full course).

---

## The North Star (M00)

**Agent vs chatbot**: a chatbot is one turn (user → LLM → reply). An agent is a *loop*: LLM thinks → calls a tool → reads the result → thinks again → repeats until done. The LLM is the brain, tools are the hands, your code is the loop.

**Agent architecture (7 building blocks)**: Brain (LLM), Tools (function calling/MCP), Memory (history + RAG + vector DB), Plan (ReAct, decomposition), Guardrails (input/output validation, HITL), Eyes (tracing, monitoring), Home (API, deployment).

**Lifecycle (5 stages)**: Design → Build → Protect → Observe → Deploy. Most tutorials stop at Build; production needs all five.

---

## Track 1 — Foundations (M01–M04, M03B)

**M01 LLM mental model**
- LLM = "world's best-read autocomplete," predicts next token from a probability distribution.
- Reads input all at once; generates output one token at a time (autoregressive).
- **Temperature** scales the probability distribution (0 = deterministic, 1 = creative). **Top-p** keeps only the smallest set of tokens whose cumulative probability ≥ p. **Top-k** keeps the K most likely.
- Mental model: a *thinker*, not a calculator. Probabilistic, not deterministic — needs guardrails.

**M02 Tokens**
- Tokens are subword units via BPE (~100K vocab). Common words = 1 token, rare/long words/emoji = several.
- Why they matter: **cost** (priced per token), **limits** (context window measured in tokens), **performance** (more tokens = slower).
- **Context window** = system prompt + history + user message + response space. Hitting the limit is hard truncation, not graceful.
- Output tokens cost more than input tokens. The response itself eats budget — always reserve room.

**M03 Prompts**
- Three roles: **system** (personality, rules), **user**, **assistant**.
- Patterns: **zero-shot** (just ask), **few-shot** (give examples), **chain-of-thought** (ask it to reason step-by-step), **role prompting** ("You are a..."), **structured output** (XML tags / JSON), **delimiters** to separate instructions from data.
- System prompts = "personality programming." Multi-turn = stateless API + you replaying history.

**M03B Context engineering** (the bridge from prompt engineering to agent engineering)
- Prompt engineering = writing the message; **context engineering = curating everything the model sees**: system + tools + history + retrieved docs + tool results + current turn.
- Four levers: **Add, Compress, Retrieve, Offload** — the organizing frame for memory work.
- **Static vs dynamic context**: order matters because prompt caching only hits on identical prefixes.
- **Position effects**: lost-in-the-middle — put critical content at the edges.
- **Context rot**: stale tool results, superseded instructions, resolved errors poison long sessions.

**M04 Structured output**
- Why agents need it: downstream code needs JSON, not prose.
- Native tool use is the cleanest path to structured output (Claude returns a typed `tool_use` block).
- Validate with Pydantic (Python) / Zod (TS). On parse failure: feed the error back and retry, don't crash.

---

## Track 2 — Tool Use (M05–M07)

**M05 Function calling — the pivotal module**
- A tool definition = `name`, `description`, `input_schema` (JSON Schema). Description quality drives selection accuracy.
- **Critical**: Claude doesn't run tools. It *asks* to. Your code executes them and returns `tool_result`. Security & control hinge on this.
- The loop: send → check `stop_reason` → if `tool_use`: run tool, send result back → repeat → exit on `end_turn`.
- Errors: return them as `tool_result` (not stack traces). Validate args before executing. Never let Claude construct arbitrary commands.

**M06 Multi-tool orchestration**
- **Parallel** tool calls when tools are independent; **sequential** chains when output A feeds B.
- Selection is description-driven — Claude picks based on what each tool's description claims it does.
- Tools can be added/removed at runtime (dynamic registration).

**M07 MCP (Model Context Protocol)**
- "USB-C for AI" — a standard protocol so any client (Claude Desktop, Claude Code) can talk to any server.
- Architecture: **Client ↔ Server ↔ Resources / Tools / Prompts**.
- **Resources** = read-only data (files, DB rows). **Tools** = actions with side effects. **Prompts** = reusable templates.
- Cert anti-pattern: hardcoded API keys in `.mcp.json` → use `${ENV_VAR}` expansion.

---

## Track 3 — Memory & Context (M08–M11)

**M08 Conversation management**
- Stateless reality: every API call is fresh. *You* replay history.
- Strategies: full history (small chats), sliding window (recent N), summarization (compress old turns).
- Token budget = system + history + user + reserved response space. Pruning = which turns to keep/drop.

**M09 RAG**
- Pipeline: **Load → Chunk → Embed → Store → Retrieve → Generate**.
- Embeddings = words/passages mapped to coordinates in meaning-space. **Cosine similarity** = angle between vectors.
- Chunking strategies: fixed-size (simple), recursive (splits on natural boundaries), semantic (by meaning).
- Vector DBs: ChromaDB (local), Pinecone (managed), pgvector (Postgres extension).

**M10 Advanced RAG**
- **Hybrid search**: BM25 keyword + vector semantic, fused (e.g., reciprocal rank fusion).
- **Re-ranking**: a second model reorders top-K retrieved chunks by relevance.
- Query transforms: **HyDE** (generate a hypothetical answer, embed *that*), **multi-query** (rephrase N times), **step-back** (ask a more general version first).
- **Contextual compression**: trim retrieved chunks to only the relevant sentences.
- Eval metrics: precision, recall, **faithfulness** (answer grounded in sources?).

**M11 Multi-layer memory**
- **Working memory** (scratchpad for current task), **episodic** (vector DB of past interactions), **procedural** (skill library of learned tool sequences).
- Summarization pipeline compresses long sessions; cross-session persistence keeps memory across runs.

---

## Track 4 — Agent Architectures (M12–M15, M15B)

**M12 ReAct loop**
- **Reason → Act → Observe → Repeat**. The canonical agent shape.
- Visible thought traces ("think out loud") improve accuracy.
- Stop conditions: natural termination via `stop_reason: end_turn`; `maxTurns` is a *safety net*, not a primary control.

**M13 Planning & decomposition**
- Big tasks need a plan. Steps: classify intent → decompose into subtasks → build a **DAG** (dependencies) → execute (parallel where possible).
- Dynamic tool discovery: pick tools at runtime based on the subtask.

**M14 Multi-agent systems**
- Patterns: **supervisor/worker** (coordinator delegates), **peer-to-peer** (agents message each other), **pipeline** (assembly line).
- Communication: shared state (DB/blackboard) vs message passing (explicit handoffs).
- Conflict resolution when agents disagree: voting, supervisor decides, escalate to human.

**M15 Code interpreter / sandboxed execution**
- Why: LLMs can't reliably do arithmetic / data manipulation — write code, run it, read output.
- Sandboxes: **Docker** (heavy, full isolation), **E2B** (managed remote sandbox), **Pyodide** (Python in browser).
- Threats: filesystem access, network egress, resource exhaustion. Always isolate.

**M15B BUILD: full agent + subagent system**
- Architecture lesson: **single agent with many tools vs coordinator + subagents** — coordinator wins when domains differ (separation of context, fewer tools per agent).
- Coordinator passes context **explicitly**, not inherited. Results flow back and are synthesized.
- Cert relevant: **4–5 tools per agent max**; distribute the rest to subagents.

---

## Track 5 — Guardrails & Safety (M16–M18)

**M16 Input guardrails**
- **PII detection/redaction** before sending to the model.
- **Prompt injection** types: **direct** (user types malicious instructions), **indirect** (malicious instructions in retrieved docs/web pages/email), **jailbreaks** (roleplay/encoding tricks). Detect patterns + sandbox untrusted content.
- Schema validation, rate limiting, abuse prevention at the boundary.

**M17 Output guardrails + HITL**
- Output checks: hallucination detection (cross-reference sources), toxicity, format validation.
- **Cost controls**: budget caps, token caps, time limits — agent loops can explode.
- HITL gates: **approval** (pause before action), **modification** (human edits), **escalation** (agent recognizes its limits).
- **Circuit breaker**: failure count → threshold → fallback path.
- Cert anti-pattern: sentiment-based escalation. Use **policy gaps, capability limits, thresholds** instead.

**M18 Evaluation & testing**
- Agent eval ≠ unit testing. Metrics: task completion rate, tool selection accuracy, response quality.
- **Claude-as-judge** = automated grading with another LLM call.
- A/B test prompts, tools, strategies. Regression-test with a frozen test set.
- Cert anti-pattern: aggregate-only accuracy → use **per-document-type stratified metrics**.

---

## Track 6 — Observability (M19–M20)

**M19 Tracing & logging**
- **Trace** = the full record of one agent run; **spans** = nested timed sub-operations (LLM call, tool call, retrieval).
- Visualize as a waterfall. Log structured fields, never PII.
- Tools: LangSmith, Langfuse (open source), Arize, OpenTelemetry.

**M20 Monitoring**
- Dashboards: latency, token usage, success/failure rates.
- **Drift detection**: behavior changes over time (prompt regressions, model updates).
- Alerting: page vs ticket — what's broken vs what's degraded.
- Feedback loops: production traces → eval set → improvements. Canary / staged rollouts for prompt changes.

---

## Track 7 — Production Deployment (M21, M22, M22B)

**M21 API design & deployment**
- Surfaces: REST (simple), WebSocket (bidirectional), **SSE/streaming** (best for slow agent responses — show progress).
- Containerize with Docker. Cloud targets: AWS Lambda (serverless), Cloud Run (managed containers), Railway.
- Scale: concurrency, queue-based processing for long jobs.

**M22 Cost optimization**
- Cost anatomy: LLM tokens + tool execution + retrieval + compute.
- **Prompt caching**: identical prefixes cached → big discount on repeated reads. Order matters (static first, dynamic last).
- **Model routing**: cheap model for easy, expensive for hard. Cache responses for common queries. Cache embeddings.
- Token diet: tighten system prompts, constrain output length.

**M22B BUILD: deploy to Local / GCP / AWS**
- Wrap as **FastAPI**: `/query`, `/query/stream` (SSE), `/health`.
- Why FastAPI: async, auto OpenAPI docs, Pydantic validation. Streaming matters because agents take 5–30s.
- Docker: multi-stage build, non-root user, secrets via env vars (never baked in).
- Same agent runs on local Docker, Cloud Run, Lambda — verified with one curl.

---

## Track 8 — Capstones & Frontier (M23, M24)

**M23** integrates capstones across three domains:
- **Domain A**: Healthcare Pre-Authorization (CPT/ICD codes, HIPAA).
- **Domain B**: B2B Ecommerce order tracking (PO lifecycle, carrier APIs, SLAs).
- **Domain C**: Public records / UCC (lien risk, entity resolution, Medallion Architecture).

**M24 What's next**
- Agent-to-agent protocols, agent marketplaces, computer use, extended thinking.
- Building responsibly: alignment, oversight, ethics.

---

## Track 9 — Cert Prep (M25, M26, M27, M27B)

**M25 Claude Code mastery (Cert Domain 3, ~20%)**
- **CLAUDE.md hierarchy** (cascades like CSS): user-level (`~/.claude/`) → project-level (`.claude/`) → directory-level. More specific wins. `@import` shares rules.
- **Slash commands vs skills**: commands are speed-dial buttons (manual); skills are auto-invoked by description match. Skills support `context: fork` (isolated context) and `allowed-tools` restrictions.
- **Plan mode**: Claude drafts → you approve → executes. Use for unfamiliar codebase, risky/complex changes. Direct execution for small, well-understood tasks.
- Patterns: **TDD** (red-green-refactor with Claude), **interview pattern** (tell Claude to ask *you* questions first), **concrete examples** (give 2–4 then generalize).
- Built-ins: Glob (find) → Read (understand) → Edit (change) → Bash (test). Grep for patterns.

**M26 Hooks, sessions, Agent SDK (Cert Domain 1, ~25% — heaviest)**
- **Agent SDK `query()`**: handles the loop, streaming, tool execution automatically. Messages API = manual loop; SDK = managed loop.
- **`stop_reason`** is the loop control: `tool_use` → continue, `end_turn` → stop, `max_tokens` → handle gracefully. **NEVER parse natural language** to detect "done."
- **Hooks** = deterministic enforcement (CODE), unlike prompts (probabilistic).
  - **PreToolUse**: run before a tool call (block, modify, redirect).
  - **PostToolUse**: run after (validate, normalize, log).
  - Use hooks for critical business rules (refund caps, PII, compliance). Use prompts for style/tone.
- **Sessions**: named (`--session`), `--resume`, `fork_session` for parallel exploration without polluting main context.

**M27 Cert exam prep — the 18 anti-patterns** (memorize these)

**Domain 1 — Agentic architecture**
1. ❌ Parsing natural language to end the loop → ✅ Check `stop_reason`.
2. ❌ Arbitrary iteration caps as primary stop → ✅ Natural termination; `maxTurns` is only a safety net.
3. ❌ Prompt-based enforcement of critical rules → ✅ Programmatic hooks.
4. ❌ Sentiment-based escalation → ✅ Policy gaps, capability limits, thresholds.
5. ❌ Self-reported confidence scores → ✅ Structured criteria + programmatic checks.

**Domain 2 — Tool design / MCP**
6. ❌ Generic errors ("Operation failed") → ✅ `isError`, `errorCategory`, `isRetryable`, context.
7. ❌ Empty results for access failures → ✅ Distinguish "denied" from "genuinely empty."
8. ❌ 18+ tools per agent → ✅ 4–5 per agent; distribute to subagents.
9. ❌ Hardcoded API keys in `.mcp.json` → ✅ `${ENV_VAR}` expansion.

**Domain 3 — Claude Code config**
10. ❌ Personal prefs in project CLAUDE.md → ✅ User-level for personal, project for team.
11. ❌ Commands for complex tasks needing isolation → ✅ Skills with `context: fork`.
12. ❌ Same-session self-review in CI → ✅ Separate sessions for generate vs review.

**Domain 4 — Prompt engineering / validation**
13. ❌ Vague instructions ("be thorough") → ✅ Explicit measurable criteria.
14. ❌ Assuming `tool_use` means semantic correctness → ✅ Schema + business-rule validation.
15. ❌ Generic retry ("try again") → ✅ Append the *specific* error (which field, expected vs actual).

**Domain 5 — Context & reliability**
16. ❌ Progressive summarization of critical details → ✅ Immutable case-facts blocks.
17. ❌ Aggregate-only accuracy → ✅ Per-document-type stratified metrics.
18. ❌ No provenance in multi-agent → ✅ Track source, confidence, timestamp, agent ID.

**Other Domain 4 essentials**
- `tool_choice`: `'auto'` (Claude picks if needed), `'any'` (must use *some* tool), forced specific tool. Know which fits.
- Schema design: required vs optional, enums with `'other'` + freetext detail, nested objects.
- **Validation-retry**: on failure append the specific error → re-request → up to ~3 tries. Track `detected_pattern` — if same field fails 3 times, escalate to human, don't loop forever.
- Multi-pass review: pass 1 per-file (style/bugs); pass 2 cross-file integration. Use **separate sessions** per pass.

**M27B Domain 5.6 deep dive (the under-covered cert topic)**
- **Provenance**: structured `{claim, source, confidence}` objects (not prose with parens). Retraction must propagate.
- **Temporal data**: `{value, valid_from, valid_to, source}`. Distinguish "as-of" vs current queries. Watch the missing-`valid_to` bug.
- **Stratified sampling for human review**: take N from each confidence bucket — beats top-N and uniform random.
- **Field-level confidence** beats document-level for high-stakes extraction; composes with stratified sampling.
- **Synthesis output buckets**: `established / contested / single-source / temporal-warning`. Paraphrase = agreement.

---

## The mental model to carry into the exam (and into production)

1. **The agent is just a loop** around a stateless LLM. Everything else is plumbing for that loop.
2. **Context is curated**, not just written. Add / Compress / Retrieve / Offload.
3. **Probabilistic ≠ enforceable.** Critical rules go in code (hooks, validators), not prompts.
4. **`stop_reason` is the source of truth** for control flow. Never parse text to decide what to do next.
5. **Tools are *your* functions**, called on Claude's request. Validate args, structure errors, never execute arbitrary code.
6. **Production = Build + Protect + Observe + Deploy**, not just Build.
7. **Provenance matters**: every claim from a multi-agent system needs source + confidence + timestamp.
