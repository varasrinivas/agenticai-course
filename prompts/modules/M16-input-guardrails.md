# M16: Input Guardrails

**Track**: 5 — Guardrails & Safety | **Position**: 16 of 30 | **Level**: Intermediate
**Prerequisites**: M05, M12
**Estimated Time**: 60-75 minutes
**Track Color**: var(--track-guardrails) / #EF4444
**SDK Tier**: 2 (dual-track). See `prompts/19-sdk-tier-policy.md`. Lab ships BOTH `solution/` (Python wrapper functions that intercept input before `client.messages.create()`) AND `solution-sdk/` (a `PreToolUse` hook in `.claude/settings.json` plus a `can_use_tool` callback passed to `ClaudeAgentOptions`). The HTML's "Why guardrails matter" section must show the same SSN-blocking guardrail implemented both ways.

## Concepts
- Why guardrails matter (animated "guardrail failure" scenarios)
- PII detection and redaction (interactive — paste text, see PII highlighted)
- Prompt injection attacks: direct injection, indirect injection, jailbreaks
- Detection and prevention strategies (animated attack flow)
- Schema validation: ensuring inputs match expected formats
- Rate limiting and abuse prevention

## Hands-On Lab
Build an input validation pipeline for the UCC agent: PII detector (SSN, credit card), injection filter (prompt injection patterns), schema validator (filing number format, state code). Test with 10 adversarial inputs.

**Two implementations**:
1. `solution/` — Python wrapper functions that run before each `client.messages.create()` call. Manual but explicit.
2. `solution-sdk/` — guardrails declared as a `PreToolUse` hook in `.claude/settings.json` (calls a Python script per tool invocation) plus a `can_use_tool` permission callback passed to `ClaudeAgentOptions`. The student sees that hooks fire automatically — no caller code change required when a new agent is added.

## Quiz Focus (5 questions)
1. What is prompt injection? (crafted input that tricks the agent into ignoring instructions)
2. What's the difference between direct and indirect injection? (direct = user input, indirect = injected via tool results/documents)
3. PII detection catches everything? (no — regex misses edge cases, ML models have false negatives)
4. Are prompts themselves guardrails? (no — prompts can be overridden, guardrails are code-level checks)
5. What should happen when a guardrail triggers? (block input, log the attempt, return safe error message)
