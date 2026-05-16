# M17: Output Guardrails & Human-in-the-Loop

**Track**: 5 — Guardrails & Safety | **Position**: 17 of 30 | **Level**: Intermediate → Advanced
**Prerequisites**: M16
**Estimated Time**: 60-75 minutes
**Track Color**: var(--track-guardrails) / #EF4444
**SDK Tier**: 2 (dual-track). Lab ships `solution/` (manual output filter wrapper + HITL approval loop) AND `solution-sdk/` (output guardrails via a `PostToolUse` hook in `.claude/settings.json`; HITL approvals via the `can_use_tool` permission callback returning `PermissionResultDeny` until a human approves out-of-band). See `prompts/19-sdk-tier-policy.md`.

## Concepts
- Output validation: hallucination detection, toxicity filtering, format verification
- Cost controls: budget limits, token caps, execution time limits (interactive cost calculator)
- Human-in-the-Loop patterns: approval gates, modification gates, escalation gates (animated workflows)
- Circuit breaker pattern: failure count → threshold → trip → fallback → cooldown → recovery
- Confidence-based routing: auto-approve (>90%), HITL review (70-90%), auto-deny (<70%)

## Hands-On Lab
Add guardrails + HITL approval to the planning agent from M13. Implement: output format validator, cost cap ($0.50/request), circuit breaker (3 failures = halt), HITL approval gate for medium-confidence UCC entity matches.

## Quiz Focus (5 questions)
1. What is a circuit breaker? (auto-stops agent after N consecutive failures, prevents cascading errors)
2. Can Claude self-evaluate its own confidence reliably? (no — confidence scores are not calibrated, use external validation)
3. What happens in a HITL approval gate? (agent pauses, human reviews, approves/denies/modifies, agent continues)
4. Same-session review is biased — why? (Claude tends to agree with its own output in the same conversation)
5. What should a cost cap do when triggered? (stop the agent loop, return partial results, log the event)
