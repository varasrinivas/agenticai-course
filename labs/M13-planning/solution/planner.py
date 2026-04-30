"""
M13 Lab — Planning & Task Decomposition (Solution)
====================================================
Complete planning agent that decomposes a goal into sub-tasks,
executes them as a DAG, and synthesizes a structured report.

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
MODEL = "claude-sonnet-4-6"


# =============================================================================
# TASK DATA STRUCTURE
# =============================================================================

@dataclass
class Task:
    """A single task in the execution plan."""
    id: str
    description: str
    tool: str
    depends_on: list[str] = field(default_factory=list)
    status: str = "pending"
    result: Optional[str] = None

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
# LOGGING HELPERS
# =============================================================================

def log_phase(phase: str, message: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"[{phase}] {message}")
    print(f"{'=' * 60}")


def log_task(task_id: str, message: str) -> None:
    print(f"\n{'─' * 60}")
    print(f"  [{task_id}] {message}")
    print(f"{'─' * 60}")


def log_detail(message: str) -> None:
    print(f"    {message}")


# =============================================================================
# AVAILABLE TOOLS (as a string for the planning prompt)
# =============================================================================

AVAILABLE_TOOLS_DESC = """
Available tools (each task must use exactly one):
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
    Returns a list of Task objects forming a DAG.
    """
    log_phase("PLAN", f"Decomposing goal: {goal}")

    planning_prompt = f"""You are a task planning agent. Your job is to decompose a research goal
into a series of sub-tasks that can be executed using available tools.

{AVAILABLE_TOOLS_DESC}

Rules:
- Each task must use exactly ONE of the available tools.
- Tasks can depend on other tasks (specify by task ID).
- A task will receive the results of its dependencies as context.
- Order tasks so dependencies come first.
- Keep the plan focused — typically 3-5 tasks for a research goal.
- Do NOT include a final "synthesize" or "write report" task — that is handled separately.

Output ONLY a valid JSON array of task objects. No explanation, no markdown fences.
Each task object must have these fields:
  "id": "task_1" (incrementing),
  "description": "what the task does",
  "tool": "tool_name",
  "depends_on": ["task_ids"]

Example for "Research filings for XYZ Corp":
[
  {{"id": "task_1", "description": "Search for UCC filings for XYZ Corp", "tool": "search_filings", "depends_on": []}},
  {{"id": "task_2", "description": "Get detailed information for each filing found", "tool": "get_filing_details", "depends_on": ["task_1"]}},
  {{"id": "task_3", "description": "Calculate risk profile for XYZ Corp", "tool": "calculate_risk", "depends_on": ["task_1"]}}
]"""

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=planning_prompt,
            messages=[{"role": "user", "content": goal}],
        )

        text = response.content[0].text.strip()

        # Strip markdown code fences if present
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()

        tasks_data = json.loads(text)

    except json.JSONDecodeError as e:
        log_detail(f"Failed to parse plan JSON: {e}")
        log_detail(f"Raw response: {text[:500]}")
        return []
    except Exception as e:
        log_detail(f"Planning failed: {e}")
        return []

    # Convert to Task objects
    tasks = []
    for t in tasks_data:
        tasks.append(
            Task(
                id=t["id"],
                description=t["description"],
                tool=t["tool"],
                depends_on=t.get("depends_on", []),
            )
        )

    # Log the plan
    log_detail(f"Created {len(tasks)} tasks:")
    for t in tasks:
        deps = f" (after {', '.join(t.depends_on)})" if t.depends_on else " (no deps)"
        log_detail(f"  {t.id}: {t.description} [tool={t.tool}]{deps}")

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

    # Build context from dependencies
    context_parts = []
    for dep_id in task.depends_on:
        if dep_id in context:
            # Truncate large results to keep context manageable
            dep_result = context[dep_id]
            if len(dep_result) > 2000:
                dep_result = dep_result[:2000] + "\n... (truncated)"
            context_parts.append(f"Results from {dep_id}:\n{dep_result}")
    context_str = "\n\n".join(context_parts) if context_parts else "No prior context."

    # Build the user message for this task
    user_message = (
        f"Task: {task.description}\n\n"
        f"Context from previous tasks:\n{context_str}\n\n"
        f"Use the {task.tool} tool to complete this task. "
        f"If you need a specific parameter from the context (like a filing number), "
        f"extract it from the context above. Return the raw tool results."
    )

    messages = [{"role": "user", "content": user_message}]

    # Mini ReAct loop — scoped to this single task
    for turn in range(5):
        try:
            response = client.messages.create(
                model=MODEL,
                max_tokens=2048,
                tools=TOOL_DEFINITIONS,
                messages=messages,
            )
        except Exception as e:
            log_detail(f"API call failed: {e}")
            return json.dumps({"error": f"API call failed: {str(e)}"})

        # If Claude is done (no more tool calls), return the text
        if response.stop_reason != "tool_use":
            final_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    final_text += block.text
            log_detail(f"Task produced text response ({len(final_text)} chars)")
            return final_text

        # Process tool calls
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                log_detail(f"Tool call: {block.name}({json.dumps(block.input)})")
                result = execute_tool(block.name, block.input)
                log_detail(
                    f"Tool result: {result[:200]}{'...' if len(result) > 200 else ''}"
                )
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    }
                )

        # Continue the conversation with tool results
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})

    return json.dumps({"error": "Task did not complete within max turns"})


def execute_plan(tasks: list[Task]) -> dict[str, str]:
    """
    Execute tasks in dependency order (topological DAG walk).
    Only execute a task when all its dependencies have completed.
    """
    log_phase("EXECUTE", f"Running {len(tasks)} tasks in dependency order")

    results: dict[str, str] = {}
    completed_ids: set[str] = set()
    failed_ids: set[str] = set()

    # DAG execution loop
    max_iterations = len(tasks) + 1  # Safety cap
    for iteration in range(max_iterations):
        # Find tasks whose dependencies failed — mark them failed too
        to_fail = [
            t
            for t in tasks
            if t.status == "pending"
            and any(d in failed_ids for d in t.depends_on)
        ]
        for t in to_fail:
            t.status = "failed"
            failed_ids.add(t.id)
            log_task(t.id, f"SKIPPED — dependency failed")

        # Find ready tasks: pending with all deps completed
        ready = [
            t
            for t in tasks
            if t.status == "pending"
            and all(d in completed_ids for d in t.depends_on)
        ]

        if not ready:
            # Nothing left to execute — either all done or all blocked
            break

        # Execute ready tasks sequentially
        for t in ready:
            t.status = "running"
            try:
                result = execute_task(t, results)
                t.status = "completed"
                t.result = result
                results[t.id] = result
                completed_ids.add(t.id)
                log_task(t.id, "COMPLETED")
            except Exception as e:
                t.status = "failed"
                failed_ids.add(t.id)
                log_task(t.id, f"FAILED: {e}")

    # Log summary
    log_detail(
        f"Execution complete: {len(completed_ids)} completed, "
        f"{len(failed_ids)} failed"
    )

    return results


# =============================================================================
# PHASE 3: SYNTHESIZE REPORT
# =============================================================================

def synthesize_report(goal: str, tasks: list[Task], results: dict[str, str]) -> str:
    """
    Ask Claude to synthesize all task results into a structured report.
    """
    log_phase("REPORT", "Synthesizing final report")

    # Gather completed task results
    results_text = ""
    for task in tasks:
        if task.status == "completed" and task.result:
            results_text += f"\n### {task.description}\n{task.result}\n"

    if not results_text.strip():
        return "No task results available to synthesize. All tasks may have failed."

    user_message = (
        f"Original research goal: {goal}\n\n"
        f"Research results from completed tasks:\n{results_text}\n\n"
        f"Write a structured risk report with these sections:\n"
        f"1. **Executive Summary** — One paragraph overview of findings\n"
        f"2. **Filing Details** — List each filing found with key details "
        f"(filing number, parties, collateral, status, dates)\n"
        f"3. **Risk Assessment** — Risk score, risk level, and contributing factors\n"
        f"4. **Recommendation** — Clear next steps based on the findings\n\n"
        f"Use specific data from the research results. "
        f"If some data was not found (e.g., no filings for the entity), note that clearly. "
        f"Be concise and professional."
    )

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            messages=[{"role": "user", "content": user_message}],
        )

        report = ""
        for block in response.content:
            if hasattr(block, "text"):
                report += block.text

        return report

    except Exception as e:
        return f"Report synthesis failed: {e}"


# =============================================================================
# MAIN — Run the full planning pipeline
# =============================================================================

def run_planning_agent(goal: str) -> str:
    """Full pipeline: Plan -> Execute -> Synthesize."""
    log_phase("START", "Planning agent initialized")
    log_detail(f"Goal: {goal}")

    # Phase 1: Create the plan
    tasks = create_plan(goal)
    if not tasks:
        return "Failed to create a plan. Check API key and model availability."

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
    if len(sys.argv) > 1:
        goal = " ".join(sys.argv[1:])
    else:
        goal = "Generate a complete risk report for Acme Corporation"

    print("=" * 60)
    print("M13 Lab — Planning & Task Decomposition (SOLUTION)")
    print("=" * 60)

    report = run_planning_agent(goal)

    print("\n" + "=" * 60)
    print("FINAL REPORT")
    print("=" * 60)
    print(report)
