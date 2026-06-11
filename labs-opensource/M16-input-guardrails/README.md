# M16 Lab: Input Guardrails

> Four layers between the user and your agent, ordered cheapest-first: rate limit (free) → PII redaction (regex, sub-ms) → injection classifier (one model call) → schema validation. And the rule that matters most: **security guardrails fail CLOSED.**

## Prerequisites

- M04 complete (Pydantic/Zod)

## Exercises (one file: `guardrail_pipeline.py` / `.js`)

| Part | What You Build | Key Concept |
|------|---------------|-------------|
| 1 | `redact_pii()` | Regex detection + the reverse-order replacement trick + Luhn check |
| 2 | `TokenBucket.consume()` | Continuous-refill rate limiting |
| 3 | `detect_injection()` | LLM-as-classifier that **fails closed** |
| 4 | `GuardrailPipeline.process()` | Layer ordering: cheap before expensive |

Provided complete: the PII regex patterns, `_luhn_check`, the `AgentRequest` schema (Pydantic/Zod), `RateLimiter` (per-user bucket management), the classifier prompt, and a 7-scenario test suite.

## Part 1: redact_pii(text) → (redacted, matches)

- Run every pattern; collect matches with `start`/`end`/`replacement`
- **Credit cards**: regex alone isn't enough — strip non-digits and run the provided `_luhn_check`; skip non-validating numbers (that's how you avoid redacting order numbers)
- **Replace in reverse order** (sort matches by `start` descending) so earlier replacements don't shift the indices of later ones — the classic bug this exercise exists to teach

## Part 2: TokenBucket.consume() → (allowed, info)

Refill first (`tokens = min(capacity, tokens + elapsed * refill_rate)`), then spend: if ≥1 token, take one and allow; else compute `retry_after = (1 - tokens) / refill_rate` and deny.

## Part 3: detect_injection(user_input)

One model call with the provided classifier prompt (returns JSON `threat_level: safe|suspicious|malicious`). Block only "malicious".

**The non-negotiable:** on ANY exception (API down, JSON parse failure) return `blocked: True`. M14's reviewer failed open because a human read the output anyway; an injection gate that fails open is an unlocked door precisely when the lock breaks.

## Part 4: Pipeline ordering

Rate limit → PII redact → injection classify **on the redacted text** (never send raw PII to the classifier model either!) → return PASS / MODIFIED / BLOCKED with layer attribution.

## Run It

```bash
python starter/guardrail_pipeline.py
```

7 scenarios: clean input, SSN, email+phone, direct injection ("Ignore all previous instructions..."), DAN role-play, clean-after-injection (proves per-user state doesn't leak), and a 6-request flood against a 5-capacity bucket.

## Gotchas

- **Mistral-7B as injection classifier is ~80-90% accurate** — it sometimes flags security QUESTIONS ("what are injection attacks?") as suspicious. That's why "suspicious" passes and only "malicious" blocks.
- **Phone regex overlaps SSN regex** for some formats; running SSN first (dict order) is the simple fix used here.

## Stretch Goals

- Add IBAN and IP-address PII patterns
- Log every BLOCKED event as JSONL (preview of M19)
- Measure the classifier's false-positive rate against 20 benign security questions
