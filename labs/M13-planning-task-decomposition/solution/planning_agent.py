"""
M13 Lab — Planning & Task Decomposition (Solution)
====================================================
Planning agent that decomposes complex queries into ordered
sub-tasks and executes them step by step.

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
# OBSERVATION HELPERS
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
# TOOL DEFINITIONS
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
                "data": {"type": "string", "description": "Raw data to summarize"}
            },
            "required": ["section_title", "data"]
        }
    }
]


# =============================================================================
# TOOL EXECUTION
# =============================================================================

def calculate_risk_for_debtor(debtor_name: str) -> dict:
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
# PLANNING AGENT — SOLUTION
# =============================================================================

PLANNING_SYSTEM_PROMPT = """You are a task planning agent. Given a complex query about UCC filings,
decompose it into 3-6 ordered steps that can be executed sequentially.

Return ONLY a JSON array of step objects. No other text.
Each step object has:
- "step_id": string like "step_1", "step_2", etc.
- "task": string describing what this step does
- "depends_on": array of step_ids that must complete before this step (can be empty)
- "tools_needed": array of tool names this step will likely use

Available tools: search_filings, get_filing_details, calculate_risk, generate_report_section

Example for "Research Acme Corp filings and assess risk":
[
  {"step_id": "step_1", "task": "Search for all UCC filings for Acme Corp", "depends_on": [], "tools_needed": ["search_filings"]},
  {"step_id": "step_2", "task": "Get detailed information for each filing found", "depends_on": ["step_1"], "tools_needed": ["get_filing_details"]},
  {"step_id": "step_3", "task": "Calculate risk profile based on filing data", "depends_on": ["step_1"], "tools_needed": ["calculate_risk"]},
  {"step_id": "step_4", "task": "Generate final risk report summarizing all findings", "depends_on": ["step_2", "step_3"], "tools_needed": ["generate_report_section"]}
]"""


def create_plan(user_query: str) -> list[dict]:
    """Ask Claude to decompose a complex query into ordered sub-tasks."""
    response = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        system=PLANNING_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_query}],
    )

    # Extract text from response
    text = ""
    for block in response.content:
        if hasattr(block, "text"):
            text += block.text

    # Parse JSON — handle potential markdown code fences
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]  # Remove first line
        text = text.rsplit("```", 1)[0]  # Remove closing fence

    try:
        plan = json.loads(text)
        if isinstance(plan, list) and len(plan) > 0:
            return plan
    except json.JSONDecodeError:
        pass

    # Fallback: single-step plan
    return [{"step_id": "step_1", "task": user_query, "depends_on": [], "tools_needed": ["search_filings"]}]


def execute_step(step: dict, context: str, max_turns: int = 5) -> str:
    """Execute a single plan step using the ReAct loop."""
    system_prompt = f"""You are executing one step of a research plan about UCC filings.

## Your Task
{step['task']}

## Context From Previous Steps
{context if context else 'This is the first step — no previous context.'}

## Instructions
- Use the available tools to complete this specific task.
- Be concise in your response — just report the findings for this step.
- If you have enough information from the context, you may skip tool calls.
"""

    messages = [{"role": "user", "content": f"Execute this step: {step['task']}"}]

    for turn in range(max_turns):
        response = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            system=system_prompt,
            tools=TOOLS,
            messages=messages,
        )

        if response.stop_reason != "tool_use":
            final_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    final_text += block.text
            return final_text

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                result = execute_tool(block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })

        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})

    return "Step did not complete within max turns."


def run_planning_agent(user_query: str) -> str:
    """Run the full planning agent: plan, then execute each step."""
    observe("QUERY", user_query)

    # Phase 1: Create the plan
    plan = create_plan(user_query)
    observe_plan(plan)

    # Phase 2: Execute each step in order
    step_results = {}
    context = ""

    for i, step in enumerate(plan, 1):
        observe_step(i, step["task"])

        result = execute_step(step, context)
        observe_step_result(i, result)

        step_results[step["step_id"]] = result

        # Build cumulative context for subsequent steps
        context += f"\n\n--- Results from Step {i}: {step['task']} ---\n{result}"

    # Phase 3: Synthesize final answer from the last step or a summary call
    if len(plan) > 1:
        # Ask Claude to synthesize all step results into a final report
        synthesis_response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system="You are a report writer. Synthesize the research results into a clear, comprehensive report.",
            messages=[{
                "role": "user",
                "content": f"Original query: {user_query}\n\nResearch results:\n{context}\n\nPlease synthesize these findings into a final report."
            }],
        )
        final = ""
        for block in synthesis_response.content:
            if hasattr(block, "text"):
                final += block.text
        observe("FINAL REPORT", final[:200] + "..." if len(final) > 200 else final)
        return final
    else:
        return step_results.get("step_1", "No results produced.")


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("M13 Lab — Planning & Task Decomposition (SOLUTION)")
    print("=" * 60)

    # Scenario 1: Single-entity risk report
    print("\n\n>>> Scenario 1: Generate risk report")
    result1 = run_planning_agent(
        "Generate a complete risk report for Greenfield Logistics LLC"
    )
    print(f"\nFINAL REPORT:\n{result1}")

    # Scenario 2: Comparative analysis
    print("\n\n>>> Scenario 2: Compare two entities")
    result2 = run_planning_agent(
        "Compare lien exposure between Nextera Holdings and Lone Star Energy"
    )
    print(f"\nFINAL REPORT:\n{result2}")
