# 🎓 Cert Tip Callouts — Add to Existing Modules

These are small callout boxes to add to existing modules wherever content maps to a certification exam topic. Use natural language editing to insert these.

**Source of truth**: Anthropic's official "Claude Certified Architect – Foundations Certification Exam Guide" (Version 0.1, Feb 10 2025). All Domain numbering below matches the official task statements:

- **Domain 1** Agentic Architecture & Orchestration (27%): 1.1 agentic loops · 1.2 hub-and-spoke multi-agent · 1.3 subagent invocation · 1.4 multi-step workflows w/ enforcement · 1.5 hooks · 1.6 task decomposition · 1.7 session state
- **Domain 2** Tool Design & MCP Integration (18%): 2.1 tool descriptions · 2.2 structured errors · 2.3 tool distribution + tool_choice · 2.4 MCP server config · 2.5 built-in tools (Read/Write/Edit/Bash/Grep/Glob)
- **Domain 3** Claude Code Configuration & Workflows (20%): 3.1 CLAUDE.md hierarchy · 3.2 commands & skills · 3.3 path-specific rules · 3.4 plan mode vs direct · 3.5 iterative refinement · 3.6 CI/CD
- **Domain 4** Prompt Engineering & Structured Output (20%): 4.1 explicit criteria · 4.2 few-shot · 4.3 tool_use schemas · 4.4 validation/retry · 4.5 batch processing · 4.6 multi-instance/multi-pass review
- **Domain 5** Context Management & Reliability (15%): 5.1 conversation context (lost-in-middle, case facts) · 5.2 escalation/ambiguity · 5.3 error propagation · 5.4 large codebase exploration · 5.5 human review + confidence calibration · 5.6 information provenance + uncertainty

**Out of scope** (per official guide, do NOT lean on these for cert prep): prompt-caching implementation details (beyond knowing it exists), token counting, API pricing, embeddings/vector DB internals, computer use, vision, streaming, OAuth, cloud-provider configs, fine-tuning.

## Format
```html
<div class="co cert" style="background:rgba(212,168,67,.06);border-left:4px solid #D4A843;border-radius:0 8px 8px 0;padding:14px 18px;margin:16px 0">
  <strong style="color:#D4A843">🎓 Cert Tip — Domain X.Y</strong><br>
  <span style="color:#94a3b8;font-size:13px">{tip content}</span>
</div>
```

## Callouts by Module

### M03 (Prompts)
**After few-shot prompting section:**
> 🎓 Cert Tip — Domain 4.1: The exam penalizes vague instructions like "be thorough" or "find all issues." Always provide explicit, measurable criteria: "flag functions exceeding 50 lines" not "flag long functions."

**After structured output section:**
> 🎓 Cert Tip — Domain 4.2: Few-shot prompting with 2-4 examples is the exam-recommended approach for ambiguous format requirements. More examples = diminishing returns.

### M04 (Structured Output)
**After JSON schema section:**
> 🎓 Cert Tip — Domain 4.3: tool_use guarantees STRUCTURE (valid JSON matching schema) but NOT semantic correctness. Values inside the JSON may still be wrong. Always add business rule validation after tool_use extraction.

**After error handling section:**
> 🎓 Cert Tip — Domain 4.4: When a validation-retry fails, append SPECIFIC error details to the prompt: which field, what was wrong, expected vs actual. Anti-pattern: generic "there were errors, please try again."

### M05 (Function Calling)
**After tool definition section:**
> 🎓 Cert Tip — Domain 2.1: Tool descriptions are critical for selection accuracy. Include: what the tool does, input format with examples, expected output format, and edge cases. Poor descriptions = Claude picks the wrong tool.

**After error handling section:**
> 🎓 Cert Tip — Domain 2.2: Return structured errors from tools: `{isError: true, errorCategory: "auth_failure", isRetryable: true, context: "Token expired"}`. Anti-pattern: generic "Operation failed" — Claude can't decide to retry, try alternatives, or escalate.

**After the tool use loop section:**
> 🎓 Cert Tip — Domain 2.2: Never silently return empty results for access failures. `{isError: false, results: []}` means "nothing found." `{isError: true, errorCategory: "access_denied"}` means "couldn't even check." Claude makes catastrophically different decisions based on which one you return.

### M06 (Multi-Tool Orchestration)
**After multi-tool section:**
> 🎓 Cert Tip — Domain 2.3: Keep 4-5 tools per agent maximum. Tool selection accuracy degrades rapidly above 5. Anti-pattern: one agent with 18+ tools. Instead, distribute tools across specialized subagents. Also know `tool_choice` options: `"auto"` (model may return text), `"any"` (model must call a tool but picks which), forced `{"type": "tool", "name": "..."}` (specific tool first).

### M07 (MCP)
**After MCP config section:**
> 🎓 Cert Tip — Domain 2.4: Never hardcode API keys in .mcp.json — these files get committed to git. Use `${ENV_VAR}` environment variable expansion. Also know the config hierarchy: `.mcp.json` (project) vs `~/.claude.json` (user).

### M08 (Conversation Management)
**After summarization section:**
> 🎓 Cert Tip — Domain 5.1: Progressive summarization loses critical specifics: names, IDs, amounts, dates. For production systems, use immutable "case facts" blocks positioned at the START of context (high-recall position). These are never summarized.

**After token budget section:**
> 🎓 Cert Tip — Domain 5.1: The "lost in the middle" effect means information in the middle of long context gets lower recall than information at the start or end. Position critical data at the beginning (case facts) or end (current query). (Both this and the case-facts tip live under Domain 5.1 in the official guide.)

### M11 (Multi-Layer Memory)
**After persistence section:**
> 🎓 Cert Tip — Domain 5.4: Long sessions accumulate stale context — Claude may reference code that's been changed. Mitigations: /compact (lossy), scratchpad files (lossless), subagent delegation (fresh context), or crash recovery manifests for interrupted sessions.

### M12 (ReAct Pattern)
**After the agentic loop section:**
> 🎓 Cert Tip — Domain 1.1: The correct way to determine loop termination is checking `stop_reason`: 'tool_use' means continue, 'end_turn' means done. CRITICAL anti-pattern: parsing Claude's natural language response to see if it says "I'm done" or "task complete."

**After stop conditions section:**
> 🎓 Cert Tip — Domain 1.1: maxTurns / iteration caps are a SAFETY NET, not a control mechanism. Anti-pattern: using an arbitrary cap (e.g., 10 iterations) as the primary stopping logic. Let the agent terminate naturally via stop_reason.

### M13 (Planning & Task Decomposition)
**After decomposition section:**
> 🎓 Cert Tip — Domain 1.6: Overly narrow task decomposition creates coverage gaps — subtasks may not cover the full scope. Overly broad decomposition = individual agents overwhelmed. The exam tests finding the right granularity. Also: prompt chaining (fixed sequential pipeline) is right for predictable multi-aspect work; dynamic adaptive decomposition is right for open-ended investigation where subtasks are discovered along the way.

### M14 (Multi-Agent Systems)
**After architecture patterns section:**
> 🎓 Cert Tip — Domain 1.2: The exam strongly favors hub-and-spoke (coordinator + subagents) over flat multi-agent architectures. Know why: single coordination point, clear context isolation, structured result aggregation, auditable decision flow.

**After communication section:**
> 🎓 Cert Tip — Domain 1.3: Subagents have ISOLATED context windows — they do NOT inherit the coordinator's full conversation. The coordinator must explicitly pass relevant context in the Task prompt. Anti-pattern: assuming subagents know everything the coordinator knows.

### M17 (Output Guardrails & HITL)
**After escalation section:**
> 🎓 Cert Tip — Domain 5.2: Escalate based on policy gaps, capability limits, explicit requests, or business thresholds. NEVER escalate based on sentiment/anger alone. An angry customer with a simple request does NOT need a human. A calm customer hitting a policy gap DOES.

**After escalation section (NEW):**
> 🎓 Cert Tip — Domain 1.4 (Programmatic Prerequisite Gates): This is sample question #1 in the official exam guide. When a specific tool sequence is required for critical business logic (e.g., verify customer identity via `get_customer` BEFORE `process_refund`), use a programmatic hook that blocks the downstream tool call until the prerequisite returns success. Prompt-based instructions ("you must call get_customer first") have a non-zero failure rate — unacceptable when errors have financial consequences. Pair with structured handoff summaries when escalating mid-process.

**After circuit breaker section:**
> 🎓 Cert Tip — Domain 5.5: Self-reported confidence scores are NOT reliable for escalation decisions. The model's internal confidence is not well-calibrated. Use structured programmatic criteria instead.

### M18 (Evaluation & Testing)
**After evaluation metrics section:**
> 🎓 Cert Tip — Domain 5.5: Aggregate accuracy metrics (e.g., "95% overall") mask per-category failures. Invoices at 70% while receipts at 99% still average 95%. Track accuracy PER DOCUMENT TYPE (stratified metrics) to catch hidden failures.

**After A/B testing section:**
> 🎓 Cert Tip — Domain 4.6: Same-session self-review creates confirmation bias — the reviewer retains the generator's reasoning context. Use SEPARATE sessions for generation and review, especially in CI/CD pipelines.

**After review-strategy section (NEW):**
> 🎓 Cert Tip — Domain 4.6: Single-pass review misses inconsistencies that span files. Use multi-pass: pass 1 = per-file local analysis (style, bugs, internal consistency), pass 2 = cross-file integration analysis (interface contracts, naming drift, duplicate logic). The exam tests whether you reach for multi-pass before single-pass.

**After feedback-loop section (NEW):**
> 🎓 Cert Tip — Domain 4.4: Track `detected_pattern` fields across runs — log which validation issues users dismiss vs. accept. Patterns of dismissals signal an over-eager rule that should be loosened; patterns of accepts signal a real issue worth automating. Anti-pattern: treating every detection as equally valid forever.

### M09 (RAG)
**After retrieval section:**
> 🎓 Cert Tip — Domain 5.6: Every claim a RAG agent makes must be tagged to its source chunk (`{claim, source_id, confidence}`). Synthesizing answers without source attribution is an exam anti-pattern — even if the answer is correct, you can't audit it later. Distinguish well-established claims (multiple sources agree) from contested claims (sources disagree) in the output.

### M11 (Multi-Layer Memory)
**After memory architecture section:**
> 🎓 Cert Tip — Domain 5.6: Facts have an "as-of" timestamp. Memory layers must distinguish *current* facts ("CEO is Alice") from *historical* facts ("CEO was Bob through 2024-Q3"). Without temporal metadata, your agent will confidently report stale facts as current. Store every fact with `{value, valid_from, valid_to, source}`.

**After session-persistence section:**
> 🎓 Cert Tip — Domain 5.4: For long-running sessions, persist a *crash recovery manifest* — a small JSON file with the active task, current step, key decisions, and pending tool calls. `/compact` is a budget tool, not a recovery tool. If a session terminates mid-task (network drop, crash, timeout), the manifest lets the next session reconstruct state without replaying the full transcript.

### M14 (Multi-Agent) — NEW
**After communication section:**
> 🎓 Cert Tip — Domain 5.3: When a subagent fails, return structured error context — not generic "search unavailable." Include `failure_type`, `attempted_query`, `partial_results`, `alternative_approaches`. Anti-pattern 1: silent suppression (`{success: true, results: []}` on failure — coordinator can't tell access failure from valid empty results). Anti-pattern 2: terminating the workflow on a single failure when partial recovery is possible.

### M17 (HITL) — NEW (continued)
**After confidence-scoring section:**
> 🎓 Cert Tip — Domain 5.5: Don't escalate based on aggregate confidence. Use *field-level* confidence — extract each field with its own score, escalate only the fields below threshold. For human review batches, use *stratified sampling*: sample N from each confidence bucket (high/med/low) so reviewers see the full distribution, not just the top-N most-confident extractions.

### M22 (Cost Optimization)
**After Batch API section:**
> 🎓 Cert Tip — Domain 4.5: For non-time-sensitive workloads (nightly evaluations, bulk extraction, retroactive scoring), use the Message Batches API: 50% cost reduction with up to a 24-hour processing window and no guaranteed latency SLA. Use `custom_id` to correlate request/response pairs. Note: Batch API does NOT support multi-turn tool calling within a single request — pre-merge checks must use synchronous calls.

### M25 (Claude Code Mastery)
**Built-in tools section:**
> 🎓 Cert Tip — Domain 2.5: Glob = file path matching by name; Grep = file content search; Edit = targeted modification by unique text match; Write = full file create/overwrite. When Edit fails on non-unique text, fallback is Read + Write. Build understanding incrementally: Grep first for entry points, then Read to follow imports.

**After CI/CD section:**
> 🎓 Cert Tip — Domain 3.6: For CI/CD, use `claude -p "<prompt>" --output-format json --json-schema schema.json`. Schema-validated output enables programmatic gating without parsing freeform text. Pair with separate sessions for generator vs. reviewer (Domain 4.6) to avoid confirmation bias.

### M26 (Hooks/Sessions/Agent SDK)
**After session management section:**
> 🎓 Cert Tip — Domain 1.7: Know `--resume <session-name>` for named continuation, `fork_session` for branched exploration from a shared baseline, and the resume-vs-fresh decision (resume when prior context is mostly valid; start fresh with injected summary when prior tool results are stale).
