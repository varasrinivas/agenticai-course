# M17 Lab: Output Guardrails & Human-in-the-Loop

> M16 guarded what comes IN; this guards what goes OUT: a hallucination detector (Mistral-as-judge), a cost budget, a circuit breaker, and an approval gate for irreversible actions.

## Prerequisites

- M16 complete

## Exercises (one file: `output_pipeline.py` / `.js`)

| Part | What You Build | Key Concept |
|------|---------------|-------------|
| 1 | `check_hallucination()` | Judge claims against sources: pass / flag / block |
| 2 | `CostTracker.can_afford()` | Pre-flight budget check (estimate BEFORE spending) |
| 3 | `CircuitBreaker` | CLOSED → OPEN → HALF_OPEN state machine |
| 4 | (Provided) `approval_gate()` | HITL pause before irreversible actions |

## Part 1: Hallucination Detector

One judge call with the provided prompt; the model classifies each claim as supported / unsupported / **contradicted**. Your decision logic:
- Any `contradicted` claim → `block` (definite error)
- ≥2 `unsupported` claims → `flag` (route to a human)
- Otherwise → `pass`
- **Judge crashed? → `flag`, not pass** — quality gates degrade to human review (compare: M16's security gate fails closed to BLOCK; M14's editorial gate failed open; three modules, three failure policies, each justified)

## Part 2: CostTracker

Local inference is free, but the same agent deployed against a cloud API isn't — the tracker uses cloud prices ($2/M in, $6/M out) so the discipline transfers. `can_afford(estimated_input, estimated_output)` must check **before** the call: `total_cost + estimated_cost <= budget`.

## Part 3: Circuit Breaker

The state machine:
- `can_execute()`: CLOSED → yes; OPEN → only if cooldown elapsed (then transition to HALF_OPEN and allow ONE test request); HALF_OPEN → no (a test is already in flight)
- `record_success()`: HALF_OPEN → CLOSED; reset failure count
- `record_failure()`: increment; at threshold → OPEN (note the time); failure while HALF_OPEN → back to OPEN with **doubled cooldown** (exponential backoff)

## Run It

```bash
python starter/output_pipeline.py
```

5 tests: a response with a contradicted date (March 15 vs March 22 in the source — must `block`), a correct response (`pass`), budget exhaustion mid-loop, the full breaker state walk (3 failures → OPEN → cooldown → HALF_OPEN → success → CLOSED), and the approval gate in auto-approve mode.

## Gotchas

- **Mistral's judge output is the flakiest JSON in this course** — claims arrive as strings, statuses get invented ("partially_supported"). Parse defensively; unknown statuses count as unsupported.
- **`can_afford` estimates, `record_usage` records actuals.** If your estimates are systematically low, you'll blow the budget — estimate high.
- **The breaker cooldown doubles only on HALF_OPEN failure**, not on the initial trip.

## Stretch Goals

- Wire all four into one `process_output()` pipeline: breaker check → generate → hallucination check → (flag → approval gate)
- Make the approval gate non-blocking: write pending approvals to a JSON file a "reviewer" script processes
- Track judge accuracy: hand-label 10 responses and compare with its verdicts
