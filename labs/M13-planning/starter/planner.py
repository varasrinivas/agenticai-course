"""
M13 Lab — Planning & Task Decomposition (Starter)
===================================================
Build a planning agent that decomposes a complex goal into sub-tasks,
executes them as a DAG (Directed Acyclic Graph), and synthesizes a report.

KEY CONCEPT: Planning agents work in three phases:
  1. PLAN  — Ask Claude to break a goal into ordered sub-tasks
  2. EXECUTE — Walk the DAG, running each task when dependencies are met
  3. SYNTHESIZE — Combine all results into a coherent output

Usage:
    python planner.py
    python planner.py "Generate a complete risk report for Acme Corporation"
"""

import json
import sys
import os
from dataclasses import dataclass, field
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import anthropic
from tools import TOOL_DEFINITIONS, execute_tool

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-20250514"


# =============================================================================
# TASK DATA STRUCTURE
# =============================================================================

@dataclass
class Task:
    """A single task in the execution plan."""
    id: str                              # e.g. "task_1"
    description: str                     # e.g. "Search for UCC filings for Acme Corporation"
    tool: str                            # e.g. "search_filings"
    depends_on: list[str] = field(default_factory=list)  # e.g. ["task_1"]
    status: str = "pending"              # pending | running | completed | failed
    result: Optional[str] = None         # tool output (JSON string)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "description": self.description,
            "tool": self.tool,
            "depends_on": self.depends_on,
            "status": self.status,
            "result": self.result,
        }


# =============================================================================
# LOGGING HELPERS (complete — do not modify)
# =============================================================================

def log_phase(phase: str, message: str) -> None:
    """Log a major phase transition."""
    print(f"\n{'=' * 60}")
    print(f"[{phase}] {message}")
    print(f"{'=' * 60}")


def log_task(task_id: str, message: str) -> None:
    """Log task-level activity."""
    print(f"\n{'─' * 60}")
    print(f"  [{task_id}] {message}")
    print(f"{'─' * 60}")


def log_detail(message: str) -> None:
    """Log supporting detail."""
    print(f"    {message}")


# =============================================================================
# AVAILABLE TOOLS (as a string for the planning prompt)
# =============================================================================

AVAILABLE_TOOLS_DESC = """
Available tools:
1. search_filings(debtor_name?, state?) — Search UCC filings by debtor name and/or state
2. get_filing_details(filing_number) — Get full details of a specific UCC filing
3. calculate_risk(debtor_name) — Calculate risk profile for a debtor based on their filings
"""


# =============================================================================
# PHASE 1: CREATE PLAN
# =============================================================================

def create_plan(goal: str) -> list[Task]:
    """
    Ask Claude to decompose the goal into an ordered list of sub-tasks.

    Each task should specify:
    - id: unique identifier (task_1, task_2, ...)
    - description: what the task does
    - tool: which tool to use (search_filings, get_filing_details, calculate_risk)
    - depends_on: list of task IDs that must complete first

    Returns a list of Task objects.
    """
    log_phase("PLAN", f"Decomposing goal: {goal}")

    # ------------------------------------------------------------------
    # TODO 1: Build the planning prompt
    #
    # HINT: Create a system prompt that tells Claude:
    #   - It is a task planning agent
    #   - It must decompose the goal into sub-tasks
    #   - Each sub-task uses one of the available tools
    #   - Tasks can depend on other tasks (DAG structure)
    #   - Output must be valid JSON array
    #
    # The JSON schema for each task:
    # {
    #   "id": "task_1",
    #   "description": "Search for UCC filings for the target company",
    #   "tool": "search_filings",
    #   "depends_on": []
    # }
    #
    # For "Generate a risk report for Acme Corporation", a good plan is:
    #   task_1: search_filings (no deps) — find all filings
    #   task_2: get_filing_details (depends on task_1) — get details of each filing
    #   task_3: calculate_risk (depends on task_1) — compute risk score
    #   task_4: synthesize (depends on task_2, task_3) — this is a special
    #           "no tool" task handled by synthesize_report(), so you can
    #           either include it in the plan or handle it separately.
    #
    # NOTE: For this lab, we handle synthesis separately in synthesize_report(),
    # so the plan should only include tool-using tasks (3 tasks).
    # ------------------------------------------------------------------
    planning_prompt = None  # Replace with your planning system prompt

    # ------------------------------------------------------------------
    # TODO 2: Call Claude to generate the plan
    #
    # HINT: Use client.messages.create() with:
    #   model=MODEL
    #   max_tokens=1024
    #   system=planning_prompt
    #   messages=[{"role": "user", "content": goal}]
    #
    # Then parse the JSON from the response text.
    # Use json.loads() — look for a JSON array in the response.
    #
    # TIP: Claude might wrap JSON in ```json ... ``` — strip that first:
    #   text = response.content[0].text
    #   text = text.strip()
    #   if text.startswith("```"):
    #       text = text.split("\n", 1)[1].rsplit("```", 1)[0]
    #   tasks_data = json.loads(text)
    # ------------------------------------------------------------------
    tasks_data = []  # Replace with your Claude API call + JSON parsing

    # ------------------------------------------------------------------
    # TODO 3: Convert the parsed JSON into Task objects
    #
    # HINT: Loop through tasks_data and create Task objects:
    #   tasks = []
    #   for t in tasks_data:
    #       tasks.append(Task(
    #           id=t["id"],
    #           description=t["description"],
    #           tool=t["tool"],
    #           depends_on=t.get("depends_on", []),
    #       ))
    #
    # Then log each task for visibility:
    #   for t in tasks:
    #       log_detail(f"{t.id}: {t.description} [tool={t.tool}, deps={t.depends_on}]")
    # ------------------------------------------------------------------
    tasks = []  # Replace with Task conversion

    return tasks


# =============================================================================
# PHASE 2: EXECUTE PLAN (DAG walk)
# =============================================================================

def execute_task(task: Task, context: dict[str, str]) -> str:
    """
    Execute a single task using a mini ReAct loop.

    Args:
        task: The Task to execute
        context: Dict of {task_id: result_string} from completed dependencies

    Returns:
        The tool result as a JSON string
    """
    log_task(task.id, f"Executing: {task.description}")

    # ------------------------------------------------------------------
    # TODO 4: Build context from dependencies
    #
    # HINT: Gather results from dependency tasks to give Claude context:
    #   context_parts = []
    #   for dep_id in task.depends_on:
    #       if dep_id in context:
    #           context_parts.append(f"Results from {dep_id}:\n{context[dep_id]}")
    #   context_str = "\n\n".join(context_parts) if context_parts else "No prior context."
    # ------------------------------------------------------------------
    context_str = "No prior context."  # Replace with your context building

    # ------------------------------------------------------------------
    # TODO 5: Run a mini ReAct loop for this task
    #
    # HINT: This is similar to M12's ReAct loop but scoped to a SINGLE task.
    #
    # 1. Build the user message:
    #    user_message = (
    #        f"Task: {task.description}\n\n"
    #        f"Context from previous tasks:\n{context_str}\n\n"
    #        f"Use the {task.tool} tool to complete this task. "
    #        f"Return the raw tool results."
    #    )
    #
    # 2. Create messages list: [{"role": "user", "content": user_message}]
    #
    # 3. Loop (max 5 turns):
    #    a. Call client.messages.create() with model, max_tokens=2048,
    #       tools=TOOL_DEFINITIONS, messages=messages
    #    b. If response.stop_reason != "tool_use":
    #       - Return the text response
    #    c. If "tool_use":
    #       - Find the tool_use block in response.content
    #       - Call execute_tool(block.name, block.input)
    #       - Log the tool call and result
    #       - Append assistant message and tool_result to messages
    #       - Continue loop
    #
    # 4. Return fallback if max turns reached
    # ------------------------------------------------------------------
    return json.dumps({"error": "Not implemented — complete TODO 5"})


def execute_plan(tasks: list[Task]) -> dict[str, str]:
    """
    Execute tasks in dependency order (topological sort / DAG walk).

    Rules:
    - Only execute a task when ALL its dependencies have status "completed"
    - If a dependency failed, mark this task as "failed" and skip it
    - Collect results in a dict keyed by task ID

    Returns:
        Dict of {task_id: result_string} for all completed tasks
    """
    log_phase("EXECUTE", f"Running {len(tasks)} tasks in dependency order")

    results: dict[str, str] = {}

    # ------------------------------------------------------------------
    # TODO 6: Implement DAG execution
    #
    # HINT: Use a loop that continues until all tasks are done.
    # On each iteration, find tasks that are "pending" and whose
    # dependencies are all "completed".
    #
    # Algorithm:
    #   completed_ids = set()
    #   failed_ids = set()
    #
    #   while True:
    #       # Find ready tasks: pending + all deps in completed_ids
    #       ready = [t for t in tasks
    #                if t.status == "pending"
    #                and all(d in completed_ids for d in t.depends_on)
    #                and not any(d in failed_ids for d in t.depends_on)]
    #
    #       # Find tasks that should be failed (dep failed)
    #       to_fail = [t for t in tasks
    #                  if t.status == "pending"
    #                  and any(d in failed_ids for d in t.depends_on)]
    #
    #       # Mark failed tasks
    #       for t in to_fail:
    #           t.status = "failed"
    #           failed_ids.add(t.id)
    #           log_task(t.id, f"SKIPPED (dependency failed)")
    #
    #       if not ready:
    #           break  # Nothing left to execute
    #
    #       # Execute ready tasks (sequentially for simplicity)
    #       for t in ready:
    #           t.status = "running"
    #           try:
    #               result = execute_task(t, results)
    #               t.status = "completed"
    #               t.result = result
    #               results[t.id] = result
    #               completed_ids.add(t.id)
    #               log_task(t.id, f"COMPLETED")
    #           except Exception as e:
    #               t.status = "failed"
    #               failed_ids.add(t.id)
    #               log_task(t.id, f"FAILED: {e}")
    #
    # Return results
    # ------------------------------------------------------------------
    return results


# =============================================================================
# PHASE 3: SYNTHESIZE REPORT
# =============================================================================

def synthesize_report(goal: str, tasks: list[Task], results: dict[str, str]) -> str:
    """
    Ask Claude to synthesize all task results into a structured report.

    The report should include:
    - Executive Summary
    - Filing Details
    - Risk Assessment
    - Recommendation
    """
    log_phase("REPORT", "Synthesizing final report")

    # ------------------------------------------------------------------
    # TODO 7: Build the synthesis prompt and call Claude
    #
    # HINT:
    # 1. Gather all completed task results into a string:
    #    results_text = ""
    #    for task in tasks:
    #        if task.status == "completed" and task.result:
    #            results_text += f"\n### {task.description}\n{task.result}\n"
    #
    # 2. Build the user message asking Claude to write a report:
    #    user_message = (
    #        f"Original goal: {goal}\n\n"
    #        f"Research results:\n{results_text}\n\n"
    #        f"Write a structured risk report with these sections:\n"
    #        f"1. Executive Summary\n"
    #        f"2. Filing Details\n"
    #        f"3. Risk Assessment\n"
    #        f"4. Recommendation\n\n"
    #        f"Use specific data from the research results. "
    #        f"If some data was not found, note that clearly."
    #    )
    #
    # 3. Call client.messages.create() with model=MODEL, max_tokens=2048,
    #    messages=[{"role": "user", "content": user_message}]
    #
    # 4. Return the text response
    # ------------------------------------------------------------------
    return "Report not implemented — complete TODO 7"


# =============================================================================
# MAIN — Run the full planning pipeline
# =============================================================================

def run_planning_agent(goal: str) -> str:
    """
    Full pipeline: Plan → Execute → Synthesize.

    Args:
        goal: The high-level goal to accomplish

    Returns:
        The final synthesized report
    """
    log_phase("START", f"Planning agent initialized")
    log_detail(f"Goal: {goal}")

    # Phase 1: Create the plan
    tasks = create_plan(goal)
    if not tasks:
        return "Failed to create a plan. Check your create_plan() implementation."

    # Phase 2: Execute the plan
    results = execute_plan(tasks)

    # Phase 3: Synthesize the report
    report = synthesize_report(goal, tasks, results)

    # Summary
    log_phase("DONE", "Planning agent complete")
    completed = sum(1 for t in tasks if t.status == "completed")
    failed = sum(1 for t in tasks if t.status == "failed")
    log_detail(f"Tasks: {completed} completed, {failed} failed, {len(tasks)} total")

    return report


if __name__ == "__main__":
    # Accept goal from command line or use default
    if len(sys.argv) > 1:
        goal = " ".join(sys.argv[1:])
    else:
        goal = "Generate a complete risk report for Acme Corporation"

    print("=" * 60)
    print("M13 Lab — Planning & Task Decomposition")
    print("=" * 60)

    report = run_planning_agent(goal)

    print("\n" + "=" * 60)
    print("FINAL REPORT")
    print("=" * 60)
    print(report)
