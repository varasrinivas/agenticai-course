# M16: Input Guardrails

**Track**: 5 — Guardrails & Safety | **Position**: 16 of 30 | **Level**: Intermediate
**Prerequisites**: M05, M12
**Estimated Time**: 60-75 minutes
**Track Color**: var(--track-guardrails) / #EF4444

## Concepts
- Why guardrails matter (animated "guardrail failure" scenarios)
- PII detection and redaction (interactive — paste text, see PII highlighted)
- Prompt injection attacks: direct injection, indirect injection, jailbreaks
- Detection and prevention strategies (animated attack flow)
- Schema validation: ensuring inputs match expected formats
- Rate limiting and abuse prevention

## Hands-On Lab
Build an input validation pipeline for the UCC agent: PII detector (SSN, credit card), injection filter (prompt injection patterns), schema validator (filing number format, state code). Test with 10 adversarial inputs.

## Quiz Focus (5 questions)
1. What is prompt injection? (crafted input that tricks the agent into ignoring instructions)
2. What's the difference between direct and indirect injection? (direct = user input, indirect = injected via tool results/documents)
3. PII detection catches everything? (no — regex misses edge cases, ML models have false negatives)
4. Are prompts themselves guardrails? (no — prompts can be overridden, guardrails are code-level checks)
5. What should happen when a guardrail triggers? (block input, log the attempt, return safe error message)
