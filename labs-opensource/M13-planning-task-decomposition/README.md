# M13 Lab: Planning & Task Decomposition

> Don't plan everything — classify first. Simple requests get a direct answer; complex ones get decomposed into a DAG of sub-tasks executed in parallel waves.

## Prerequisites

- M12 complete

## Exercises (one file: `planning_agent.py` / `.js`)

| Part | Function | What You Build |
|------|----------|---------------|
| 1 | `classify_intent()` | JSON-only intent classifier (direct / research / multi_step) |
| 2 | `_validate_dag()` | Cycle detection via topological sort (pure algorithm, no LLM) |
| 3 | `execute_dag()` | Wave-based executor: parallel where deps allow |

Provided complete: `decompose_task()` (with its JSON-parse fallback), the simulated `execute_task()`, `print_plan()` visualization, the full `planning_pipeline()` orchestrator, and the test harness.

## Part 1: classify_intent

One model call, JSON-only response: `{"intent": "direct|research|multi_step", "complexity": "simple|moderate|complex", "needs_planning": true/false, "reason": "..."}`.

**The error-handling lesson:** on `JSONDecodeError`, return a safe default (`direct`, no planning) — a broken classifier should degrade to "just answer it", never crash the pipeline.

## Part 2: _validate_dag (no LLM — pure algorithm)

Kahn's topological sort: compute in-degrees from `depends_on`, repeatedly pop zero-degree tasks and decrement their dependents. If you visit fewer tasks than exist, there's a cycle. The LLM *will* occasionally emit circular dependencies — this is your seatbelt.

## Part 3: execute_dag

```
while tasks remain:
    ready = tasks whose depends_on are ALL completed (and none failed)
    if none ready → mark the rest "blocked", break    ← deadlock guard
    run all ready tasks concurrently (asyncio.gather / Promise.all)
    record results; failures go into the failed set
```

Tasks with no mutual dependencies run in the same "wave" — the visual output shows `Wave 1 [PARALLEL]: ['task_1', 'task_2']`.

## Run It

```bash
python starter/planning_agent.py
```

Three tests: "What is 2+2?" (must SKIP planning), a 3-part research request (must decompose + execute in waves), and two hardcoded DAGs (one valid, one cyclic) for your validator.

## Gotchas

- **Mistral wraps JSON in ``` fences** roughly a third of the time. The provided `_parse_json` helper strips them — use it in `classify_intent` too.
- **The "system" parameter doesn't exist** in `chat.completions.create()` — system prompts go in the `messages` array. (The course HTML has this wrong; the lab is correct.)
- **`asyncio.gather(..., return_exceptions=True)`** — without it, one failed task kills the whole wave.

## Stretch Goals

- Replace the simulated `execute_task` with real tool calls (reuse M06's registry)
- Add re-planning: if a task fails, ask the model to propose an alternative sub-task
- Render the DAG with ASCII art showing the dependency arrows
