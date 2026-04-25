# 🎓 Cert Tip Callouts — Add to Existing Modules

These are small callout boxes to add to existing modules (M01-M24) wherever content maps to a certification exam topic. Use the `/generate-phase` or natural language editing to insert these.

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
> 🎓 Cert Tip — Domain 2.3: Never silently return empty results for access failures. `{isError: false, results: []}` means "nothing found." `{isError: true, errorCategory: "access_denied"}` means "couldn't even check." Claude makes catastrophically different decisions based on which one you return.

### M06 (Multi-Tool Orchestration)
**After multi-tool section:**
> 🎓 Cert Tip — Domain 2.4: Keep 4-5 tools per agent maximum. Tool selection accuracy degrades rapidly above 5. Anti-pattern: one agent with 18+ tools. Instead, distribute tools across specialized subagents.

### M07 (MCP)
**After MCP config section:**
> 🎓 Cert Tip — Domain 2.5: Never hardcode API keys in .mcp.json — these files get committed to git. Use `${ENV_VAR}` environment variable expansion. Also know the config hierarchy: `.mcp.json` (project) vs `~/.claude.json` (user).

### M08 (Conversation Management)
**After summarization section:**
> 🎓 Cert Tip — Domain 5.1: Progressive summarization loses critical specifics: names, IDs, amounts, dates. For production systems, use immutable "case facts" blocks positioned at the START of context (high-recall position). These are never summarized.

**After token budget section:**
> 🎓 Cert Tip — Domain 5.2: The "lost in the middle" effect means information in the middle of long context gets lower recall than information at the start or end. Position critical data at the beginning (case facts) or end (current query).

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
> 🎓 Cert Tip — Domain 1.5: Overly narrow task decomposition creates coverage gaps — subtasks may not cover the full scope. Overly broad decomposition = individual agents overwhelmed. The exam tests finding the right granularity.

### M14 (Multi-Agent Systems)
**After architecture patterns section:**
> 🎓 Cert Tip — Domain 1.2: The exam strongly favors hub-and-spoke (coordinator + subagents) over flat multi-agent architectures. Know why: single coordination point, clear context isolation, structured result aggregation, auditable decision flow.

**After communication section:**
> 🎓 Cert Tip — Domain 1.3: Subagents have ISOLATED context windows — they do NOT inherit the coordinator's full conversation. The coordinator must explicitly pass relevant context in the Task prompt. Anti-pattern: assuming subagents know everything the coordinator knows.

### M17 (Output Guardrails & HITL)
**After escalation section:**
> 🎓 Cert Tip — Domain 5.3: Escalate based on policy gaps, capability limits, explicit requests, or business thresholds. NEVER escalate based on sentiment/anger alone. An angry customer with a simple request does NOT need a human. A calm customer hitting a policy gap DOES.

**After circuit breaker section:**
> 🎓 Cert Tip — Domain 1.4: Self-reported confidence scores are NOT reliable for escalation decisions. The model's internal confidence is not well-calibrated. Use structured programmatic criteria instead.

### M18 (Evaluation & Testing)
**After evaluation metrics section:**
> 🎓 Cert Tip — Domain 5.6: Aggregate accuracy metrics (e.g., "95% overall") mask per-category failures. Invoices at 70% while receipts at 99% still average 95%. Track accuracy PER DOCUMENT TYPE (stratified metrics) to catch hidden failures.

**After A/B testing section:**
> 🎓 Cert Tip — Domain 4.5: Same-session self-review creates confirmation bias — the reviewer retains the generator's reasoning context. Use SEPARATE sessions for generation and review, especially in CI/CD pipelines.
