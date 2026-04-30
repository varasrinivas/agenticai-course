"""
M13 Lab — Planning & Task Decomposition (Starter)
===================================================
Build a planning agent that decomposes complex queries into
ordered sub-tasks, then executes each step using a ReAct loop.

KEY CONCEPT: The "plan-then-act" pattern separates THINKING
from DOING. First, ask Claude to create a plan (list of steps
with dependencies). Then execute each step one at a time,
feeding results from earlier steps into later ones. This is
more reliable than letting the agent improvise on every turn.

Usage:
    python planning_agent.py
"""

import json
import sys
import os
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import anthropic
from shared.mock_ucc_data import search_filings, get_filing_by_number

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-6"


# =============================================================================
# OBSERVATION HELPERS (complete — do not modify)
# =============================================================================

def observe(label: str, message: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"[{label}] {message}")
    print(f"{'=' * 60}")


def observe_plan(plan: list[dict]) -> None:
    print(f"\n{'=' * 60}")
    print("[PLAN] Decomposed into steps:")
    for i, step in enumerate(plan, 1):
        deps = step.get("depends_on", [])
        dep_str = f" (depends on: {', '.join(deps)})" if deps else ""
        print(f"  {i}. {step['task']}{dep_str}")
    print(f"{'=' * 60}")


def observe_step(step_num: int, task: str) -> None:
    print(f"\n{'─' * 60}")
    print(f"[STEP {step_num}] Executing: {task}")
    print(f"{'─' * 60}")


def observe_step_result(step_num: int, result: str) -> None:
    print(f"\n{'─' * 60}")
    print(f"[STEP {step_num} RESULT]")
    if len(result) > 300:
        print(result[:300] + "\n... (truncated)")
    else:
        print(result)
    print(f"{'─' * 60}")


# =============================================================================
# TOOL DEFINITIONS (complete — do not modify)
# =============================================================================

TOOLS = [
    {
        "name": "search_filings",
        "description": "Search UCC filings by debtor name and/or state.",
        "input_schema": {
            "type": "object",
            "properties": {
                "debtor_name": {"type": "string", "description": "Debtor name to search for"},
                "state": {"type": "string", "description": "State to filter by"}
            },
            "required": []
        }
    },
    {
        "name": "get_filing_details",
        "description": "Get full details of a specific UCC filing by filing number.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filing_number": {"type": "string", "description": "The UCC filing number"}
            },
            "required": ["filing_number"]
        }
    },
    {
        "name": "calculate_risk",
        "description": "Calculate risk profile for a debtor based on their UCC filings.",
        "input_schema": {
            "type": "object",
            "properties": {
                "debtor_name": {"type": "string", "description": "Debtor name to assess"}
            },
            "required": ["debtor_name"]
        }
    },
    {
        "name": "generate_report_section",
        "description": "Generate a section of a risk report. Provide a section title and the data to summarize.",
        "input_schema": {
            "type": "object",
            "properties": {
                "section_title": {"type": "string", "description": "Title for this report section"},
                "data": {"type": "string", "description": "Raw data/findings to summarize in this section"}
            },
            "required": ["section_title", "data"]
        }
    }
]


# =============================================================================
# TOOL EXECUTION (complete — do not modify)
# =============================================================================

def calculate_risk_for_debtor(debtor_name: str) -> dict:
    """Analyze all filings for a debtor and return a risk profile."""
    filings = search_filings(debtor_name=debtor_name)
    if not filings:
        return {"debtor": debtor_name, "risk_score": 0, "risk_level": "UNKNOWN",
                "message": f"No filings found for '{debtor_name}'"}
    active = [f for f in filings if f["status"] == "Active"]
    blanket = [f for f in filings if "all assets" in f["collateral_description"].lower()
               or "all accounts" in f["collateral_description"].lower()]
    amendments = [f for f in filings if f["type"] == "UCC-3"]
    score = min(1.0, (len(active) * 0.25) + (len(blanket) * 0.3) + (len(amendments) * 0.1))
    if score >= 0.7:
        level, rec = "HIGH", "Significant lien exposure. Detailed due diligence required."
    elif score >= 0.4:
        level, rec = "MEDIUM", "Moderate lien activity. Review collateral descriptions."
    else:
        level, rec = "LOW", "Limited lien exposure. Standard procedures sufficient."
    return {"debtor": debtor_name, "risk_score": round(score, 2), "risk_level": level,
            "total_filings": len(filings), "active_filings": len(active),
            "blanket_liens": len(blanket), "amendments": len(amendments),
            "recommendation": rec}


def execute_tool(tool_name: str, tool_input: dict) -> str:
    """Dispatch a tool call. Returns JSON string."""
    try:
        if tool_name == "search_filings":
            results = search_filings(
                debtor_name=tool_input.get("debtor_name"),
                state=tool_input.get("state")
            )
            return json.dumps([{
                "filing_number": f["filing_number"],
                "debtor": f["debtor"]["name"],
                "secured_party": f["secured_party"]["name"],
                "state": f["state"], "status": f["status"], "type": f["type"],
                "collateral": f["collateral_description"][:120] + "..."
            } for f in results], indent=2)
        elif tool_name == "get_filing_details":
            filing = get_filing_by_number(tool_input["filing_number"])
            if filing:
                return json.dumps(filing, indent=2, default=str)
            return json.dumps({"error": f"Filing {tool_input['filing_number']} not found"})
        elif tool_name == "calculate_risk":
            return json.dumps(calculate_risk_for_debtor(tool_input["debtor_name"]), indent=2)
        elif tool_name == "generate_report_section":
            # This tool just passes the data through — Claude synthesizes in context
            return json.dumps({
                "section": tool_input["section_title"],
                "content": f"[Report section '{tool_input['section_title']}' generated from provided data]",
                "data_received": tool_input["data"][:200] + "..."
            }, indent=2)
        else:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})
    except Exception as e:
        return json.dumps({"error": f"Tool failed: {str(e)}"})


# =============================================================================
# PLANNING AGENT — YOUR CODE HERE
# =============================================================================

def create_plan(user_query: str) -> list[dict]:
    """
    Ask Claude to decompose a complex query into ordered sub-tasks.

    Returns a list of step dicts, each with:
    - "step_id": unique identifier (e.g. "step_1")
    - "task": description of what this step does
    - "depends_on": list of step_ids that must complete first (can be empty)
    - "tools_needed": list of tool names this step will likely use

    Example output:
    [
        {"step_id": "step_1", "task": "Search for all UCC filings for the company",
         "depends_on": [], "tools_needed": ["search_filings"]},
        {"step_id": "step_2", "task": "Get full details for each filing found",
         "depends_on": ["step_1"], "tools_needed": ["get_filing_details"]},
        ...
    ]
    """
    # ------------------------------------------------------------------
    # TODO 1: Implement create_plan()
    #   - Call client.messages.create() with a system prompt that instructs
    #     Claude to decompose the query into 3-6 ordered steps
    #   - The system prompt should specify the output format (JSON array)
    #   - Parse the JSON from Claude's response
    #   - Return the list of step dicts
    #   - If parsing fails, return a single-step fallback plan
    #
    # Hint for the system prompt:
    #   "You are a task planning agent. Given a complex query, decompose it
    #    into 3-6 ordered steps. Return ONLY a JSON array of step objects.
    #    Each step has: step_id, task, depends_on (list of step_ids), tools_needed.
    #    Available tools: search_filings, get_filing_details, calculate_risk,
    #    generate_report_section."
    # ------------------------------------------------------------------
    pass


def execute_step(step: dict, context: str, max_turns: int = 5) -> str:
    """
    Execute a single plan step using the ReAct loop from M12.

    Args:
        step: The step dict from the plan
        context: Results from previous steps (passed as additional context)
        max_turns: Max tool-use iterations for this step

    Returns:
        The text result from executing this step
    """
    # ------------------------------------------------------------------
    # TODO 2: Implement execute_step()
    #   - Build a system prompt that includes:
    #     a) The step's task description
    #     b) Context from previous steps
    #     c) Instructions to use tools as needed and return a concise result
    #   - Run a ReAct loop (like M12) for max_turns iterations
    #   - Return the final text response
    # ------------------------------------------------------------------
    pass


def run_planning_agent(user_query: str) -> str:
    """
    Run the full planning agent:
    1. Create a plan (decompose query into steps)
    2. Execute each step in order, passing results forward
    3. Return the final synthesized result

    Args:
        user_query: The user's complex query

    Returns:
        The final combined result from all steps
    """
    observe("QUERY", user_query)

    # ------------------------------------------------------------------
    # TODO 3: Implement run_planning_agent()
    #   - Call create_plan(user_query) to get the step list
    #   - Log the plan with observe_plan(plan)
    #   - Initialize a results dict and context string
    #   - For each step in the plan:
    #     a) Log with observe_step(step_num, step["task"])
    #     b) Call execute_step(step, context)
    #     c) Log with observe_step_result(step_num, result)
    #     d) Store the result and append to context
    #   - After all steps, synthesize a final answer
    #     (either use the last step's result or call Claude once more)
    #   - Return the final answer
    # ------------------------------------------------------------------
    pass


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("M13 Lab — Planning & Task Decomposition")
    print("=" * 60)

    # Scenario 1: Single-entity risk report
    print("\n\n>>> Scenario 1: Generate risk report")
    result1 = run_planning_agent(
        "Generate a complete risk report for Greenfield Logistics LLC"
    )
    print(f"\nFINAL REPORT:\n{result1}")

    # Scenario 2: Comparative analysis (requires parallel-ish research)
    print("\n\n>>> Scenario 2: Compare two entities")
    result2 = run_planning_agent(
        "Compare lien exposure between Nextera Holdings and Lone Star Energy"
    )
    print(f"\nFINAL REPORT:\n{result2}")
