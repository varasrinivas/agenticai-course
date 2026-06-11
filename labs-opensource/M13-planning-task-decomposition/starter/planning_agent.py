"""
M13 Lab: Planning Agent — Classify → Decompose → DAG Execute
=============================================================
Run: python planning_agent.py
"""

import asyncio
import json
import time

from openai import OpenAI

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")


def _parse_json(raw: str):
    """(COMPLETE) Parse model JSON output, stripping markdown fences."""
    raw = (raw or "").strip()
    for fence in ("```json", "```"):
        raw = raw.removeprefix(fence)
    raw = raw.removesuffix("```").strip()
    return json.loads(raw)


# ── Part 1: Intent Classifier (YOUR JOB) ─────────────────────
CLASSIFY_SYSTEM = (
    "Classify the user request. Respond with JSON only:\n"
    '{"intent": "direct|research|multi_step", '
    '"complexity": "simple|moderate|complex", '
    '"needs_planning": true/false, '
    '"reason": "one sentence why"}'
)


def classify_intent(request: str) -> dict:
    """Classify whether a request needs planning or a direct answer.

    TODO:
    1. Call the model (max_tokens=256) with CLASSIFY_SYSTEM as a SYSTEM
       message (note: there is no `system=` kwarg in the OpenAI SDK —
       it goes in the messages array) and the request as the user message
    2. Return _parse_json(content)
    3. On json.JSONDecodeError (or any parse failure): return the safe default
       {"intent": "direct", "complexity": "simple", "needs_planning": False,
        "reason": "Parse error, defaulting to direct"}
       — a broken classifier degrades to "just answer it", never crashes
    """
    pass  # Remove this line when you add your code


# ── Task Decomposer (COMPLETE) ───────────────────────────────
DECOMPOSE_SYSTEM = (
    "Decompose this goal into 3-7 sub-tasks. Respond with JSON only:\n"
    '[{"id": "task_1", "description": "...", "depends_on": [], '
    '"tools_needed": ["search", "analyze"]}, ...]'
    "\n\nRules:\n"
    "- Each task should be achievable in 1-2 tool calls\n"
    "- depends_on lists task IDs that must complete first\n"
    "- Independent tasks should have empty depends_on (they run in parallel)\n"
    "- NO circular dependencies"
)


def decompose_task(goal: str) -> list[dict]:
    """Break a complex goal into a DAG of sub-tasks."""
    try:
        response = client.chat.completions.create(
            model="mistral",
            max_tokens=1024,
            messages=[
                {"role": "system", "content": DECOMPOSE_SYSTEM},
                {"role": "user", "content": f"Goal: {goal}"},
            ],
        )
        tasks = _parse_json(response.choices[0].message.content)
        if not _validate_dag(tasks):
            print("  WARNING: cycle detected in task DAG — falling back to single task")
            return [{"id": "task_1", "description": goal, "depends_on": [], "tools_needed": []}]
        return tasks
    except Exception:
        return [{"id": "task_1", "description": goal, "depends_on": [], "tools_needed": []}]


# ── Part 2: DAG Validation (YOUR JOB — pure algorithm, no LLM) ──
def _validate_dag(tasks: list[dict]) -> bool:
    """Check for circular dependencies via Kahn's topological sort.

    TODO:
    1. in_degree = {task id: len(depends_on)} for every task
       deps = {task id: set(depends_on)}
    2. queue = all ids with in_degree 0; visited = 0
    3. While queue: pop an id, visited += 1; for every OTHER task that
       depends on the popped id, decrement its in_degree; if it hits 0,
       add it to the queue
    4. Return visited == len(tasks)   ← fewer visited ⇒ a cycle exists
    """
    pass  # Remove this line when you add your code


# ── Task Executor (COMPLETE — simulated) ─────────────────────
async def execute_task(task: dict) -> dict:
    """Execute a single sub-task (simulated)."""
    await asyncio.sleep(0.5)  # simulate work
    return {
        "task_id": task["id"],
        "status": "completed",
        "result": f"Completed: {task['description'][:60]}",
    }


# ── Part 3: DAG Executor (YOUR JOB) ──────────────────────────
async def execute_dag(tasks: list[dict], verbose: bool = True) -> list[dict]:
    """Execute tasks respecting dependencies, parallelizing where possible.

    TODO:
    completed = {}; failed = set(); results = []
    remaining = {t["id"]: t for t in tasks}; wave = 0
    While remaining:
      1. wave += 1
      2. ready = tasks in remaining whose depends_on are ALL in completed
         AND none of whose depends_on are in failed
      3. If not ready: every remaining task is blocked —
         append {"task_id": tid, "status": "blocked",
                 "result": "Blocked by failed dependency"} for each, break
      4. If verbose: print(f"    Wave {wave} "
         f"[{'PARALLEL' if len(ready) > 1 else 'SEQUENTIAL'}]: {[t['id'] for t in ready]}")
      5. wave_results = await asyncio.gather(*[execute_task(t) for t in ready],
                                             return_exceptions=True)
         ← return_exceptions=True or one failure kills the whole wave!
      6. For (task, result) pairs: if isinstance(result, Exception) →
         failed.add(id) + append a "failed" record; else completed[id] = result
         + append it. Either way: del remaining[task["id"]]
    Return results
    """
    pass  # Remove this line when you add your code


# ── Progress Visualization (COMPLETE) ────────────────────────
def print_plan(tasks: list[dict], results: list[dict] = None) -> None:
    status_map = {r["task_id"]: r["status"] for r in (results or [])}
    print("\n  Execution Plan:")
    for t in tasks:
        status = status_map.get(t["id"], "pending")
        icon = {"completed": "[done]", "failed": "[FAIL]", "blocked": "[blocked]"}.get(status, "[ .. ]")
        deps = f" (after: {', '.join(t.get('depends_on', []))})" if t.get("depends_on") else " (no deps)"
        print(f"    {icon} {t['id']}: {t['description'][:50]}{deps}")


# ── Full Pipeline (COMPLETE) ─────────────────────────────────
async def planning_pipeline(request: str, verbose: bool = True) -> str:
    """Classify → (Plan → Execute → Synthesize) or Direct Answer."""
    if verbose:
        print(f"\n{'=' * 55}\n  Request: {request}\n{'=' * 55}")

    classification = classify_intent(request)
    if verbose:
        print(f"\n  Classification: {classification['intent']} ({classification['complexity']})")
        print(f"     Needs planning: {classification['needs_planning']} — {classification['reason']}")

    if not classification["needs_planning"]:
        if verbose:
            print("  -> Routing to direct answer (no planning overhead)")
        response = client.chat.completions.create(
            model="mistral", max_tokens=1024,
            messages=[{"role": "user", "content": request}],
        )
        return response.choices[0].message.content

    if verbose:
        print("\n  Decomposing into sub-tasks...")
    tasks = decompose_task(request)
    if verbose:
        print_plan(tasks)
        print(f"\n  Executing {len(tasks)} tasks...")

    start = time.time()
    results = await execute_dag(tasks, verbose=verbose)
    elapsed = time.time() - start

    if verbose:
        print_plan(tasks, results)
        done = sum(1 for r in results if r["status"] == "completed")
        print(f"\n  Completed {done}/{len(tasks)} tasks in {elapsed:.1f}s")

    result_text = "\n".join(f"- {r['task_id']}: {r['result']}" for r in results)
    response = client.chat.completions.create(
        model="mistral", max_tokens=1024,
        messages=[{"role": "user", "content":
            f"Original request: {request}\n\nSub-task results:\n{result_text}\n\n"
            "Synthesize a final answer from these results."}],
    )
    return response.choices[0].message.content


# ── Tests (COMPLETE) ─────────────────────────────────────────
async def main():
    print("\n> TEST 1: Simple task (should skip planning)")
    r1 = await planning_pipeline("What is 2 + 2?")
    print(f"\n  Answer: {r1[:120]}")

    print("\n> TEST 2: Complex task (planning + execution)")
    r2 = await planning_pipeline(
        "Research the top 3 AI agent frameworks, compare their features, "
        "and draft a recommendation for a startup team."
    )
    print(f"\n  Answer: {r2[:200]}...")

    print("\n> TEST 3: DAG validation (pure algorithm)")
    valid = _validate_dag([
        {"id": "a", "depends_on": []},
        {"id": "b", "depends_on": ["a"]},
        {"id": "c", "depends_on": ["a"]},
        {"id": "d", "depends_on": ["b", "c"]},
    ])
    print(f"  Valid DAG (expect True):    {valid}")

    cyclic = _validate_dag([
        {"id": "a", "depends_on": ["c"]},
        {"id": "b", "depends_on": ["a"]},
        {"id": "c", "depends_on": ["b"]},
    ])
    print(f"  Cyclic DAG (expect False):  {cyclic}")


if __name__ == "__main__":
    asyncio.run(main())
