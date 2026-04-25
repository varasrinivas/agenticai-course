"""
M14 Lab — Multi-Agent Systems (Solution)
==========================================
4-agent content pipeline orchestrated by a coordinator.

Usage:
    python multi_agent.py
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
MODEL = "claude-sonnet-4-20250514"


# =============================================================================
# OBSERVATION HELPERS
# =============================================================================

def observe(label: str, message: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"[{label}] {message}")
    print(f"{'=' * 60}")


def observe_agent(agent_name: str, action: str) -> None:
    print(f"\n{'─' * 60}")
    print(f"[AGENT: {agent_name}] {action}")
    print(f"{'─' * 60}")


def observe_handoff(from_agent: str, to_agent: str, data_size: int) -> None:
    print(f"\n{'─' * 60}")
    print(f"[HANDOFF] {from_agent} → {to_agent} ({data_size} chars)")
    print(f"{'─' * 60}")


# =============================================================================
# TOOLS
# =============================================================================

RESEARCH_TOOLS = [
    {
        "name": "search_filings",
        "description": "Search UCC filings by debtor name and/or state.",
        "input_schema": {
            "type": "object",
            "properties": {
                "debtor_name": {"type": "string", "description": "Debtor name"},
                "state": {"type": "string", "description": "State filter"}
            },
            "required": []
        }
    },
    {
        "name": "get_filing_details",
        "description": "Get full details of a specific UCC filing.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filing_number": {"type": "string", "description": "The filing number"}
            },
            "required": ["filing_number"]
        }
    }
]

ANALYSIS_TOOLS = [
    {
        "name": "calculate_risk",
        "description": "Calculate risk profile for a debtor.",
        "input_schema": {
            "type": "object",
            "properties": {
                "debtor_name": {"type": "string", "description": "Debtor name"}
            },
            "required": ["debtor_name"]
        }
    }
]


# =============================================================================
# TOOL EXECUTION
# =============================================================================

def calculate_risk_for_debtor(debtor_name: str) -> dict:
    filings = search_filings(debtor_name=debtor_name)
    if not filings:
        return {"debtor": debtor_name, "risk_score": 0, "risk_level": "UNKNOWN"}
    active = [f for f in filings if f["status"] == "Active"]
    blanket = [f for f in filings if "all assets" in f["collateral_description"].lower()
               or "all accounts" in f["collateral_description"].lower()]
    amendments = [f for f in filings if f["type"] == "UCC-3"]
    score = min(1.0, (len(active) * 0.25) + (len(blanket) * 0.3) + (len(amendments) * 0.1))
    level = "HIGH" if score >= 0.7 else "MEDIUM" if score >= 0.4 else "LOW"
    return {"debtor": debtor_name, "risk_score": round(score, 2), "risk_level": level,
            "total_filings": len(filings), "active_filings": len(active),
            "blanket_liens": len(blanket), "amendments": len(amendments)}


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
            return json.dumps({"error": "Not found"})
        elif tool_name == "calculate_risk":
            return json.dumps(calculate_risk_for_debtor(tool_input["debtor_name"]), indent=2)
        else:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})
    except Exception as e:
        return json.dumps({"error": str(e)})


# =============================================================================
# SUBAGENT RUNNER — SOLUTION
# =============================================================================

def run_subagent(agent_name: str, system_prompt: str, task: str,
                 tools: list = None, max_turns: int = 5) -> str:
    """Run a specialist subagent with isolated context."""
    observe_agent(agent_name, f"Starting task: {task[:100]}...")

    messages = [{"role": "user", "content": task}]

    # If no tools, just make one call
    if not tools:
        response = client.messages.create(
            model=MODEL, max_tokens=4096, system=system_prompt, messages=messages
        )
        text = ""
        for block in response.content:
            if hasattr(block, "text"):
                text += block.text
        observe_agent(agent_name, f"Complete ({len(text)} chars)")
        return text

    # With tools: ReAct loop
    for turn in range(max_turns):
        response = client.messages.create(
            model=MODEL, max_tokens=4096, system=system_prompt,
            tools=tools, messages=messages
        )

        if response.stop_reason != "tool_use":
            text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    text += block.text
            observe_agent(agent_name, f"Complete ({len(text)} chars)")
            return text

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

    observe_agent(agent_name, "Hit max turns — returning partial result")
    return f"{agent_name} did not complete within {max_turns} turns."


# =============================================================================
# SPECIALIST AGENTS — SOLUTION
# =============================================================================

def run_researcher(task: str) -> str:
    """Research agent — gathers raw filing data."""
    system_prompt = """You are a UCC filing researcher. Your job is to search for and gather
raw filing data. Use search_filings to find filings, then get_filing_details for each one.

Report your findings as structured data: list each filing with its number, debtor, secured party,
state, status, type, filing date, and collateral description. Be thorough but concise."""

    return run_subagent("Researcher", system_prompt, task, RESEARCH_TOOLS)


def run_analyst(task: str, research_data: str) -> str:
    """Analyst agent — identifies patterns and risk from research data."""
    system_prompt = """You are a UCC filing analyst. You receive raw research data and identify
patterns, risks, and key insights. Use calculate_risk to get quantitative risk scores.

Focus on: number of liens, collateral breadth (blanket vs specific), secured party concentration,
filing freshness, and amendment history. Provide specific numbers and comparisons."""

    # EXPLICIT context passing — the analyst gets the research data in the task
    full_task = f"""{task}

## Research Data (from Researcher agent)
{research_data}"""

    return run_subagent("Analyst", system_prompt, full_task, ANALYSIS_TOOLS)


def run_writer(task: str, analysis: str) -> str:
    """Writer agent — generates a report from analysis."""
    system_prompt = """You are a professional report writer specializing in UCC lien analysis.
You receive analysis findings and write a clear, well-structured report.

Format: Use headers, bullet points, and a summary section. Include specific filing numbers
and data points. End with a clear recommendation."""

    full_task = f"""{task}

## Analysis Findings (from Analyst agent)
{analysis}

Write a clear, professional report based on these findings."""

    return run_subagent("Writer", system_prompt, full_task, tools=None)


def run_reviewer(task: str, report: str) -> str:
    """Reviewer agent — checks report quality and accuracy."""
    system_prompt = """You are a quality reviewer for UCC filing reports. Check for:
1. Accuracy — are filing numbers and data points correct?
2. Completeness — are all relevant findings included?
3. Clarity — is the report well-organized and easy to understand?
4. Actionability — does the recommendation follow from the data?

If the report is good, return it with a brief "Review: APPROVED" header.
If it needs fixes, note the issues and return a corrected version."""

    full_task = f"""Review this UCC filing report for accuracy and completeness.

Original request: {task}

## Report to Review
{report}"""

    return run_subagent("Reviewer", system_prompt, full_task, tools=None)


# =============================================================================
# COORDINATOR — SOLUTION
# =============================================================================

def run_coordinator(user_query: str) -> str:
    """Orchestrate the 4-agent pipeline."""
    observe("COORDINATOR", f"Received query: {user_query}")

    # Step 1: Research — gather raw data
    observe("COORDINATOR", "Phase 1: Dispatching Researcher")
    research_data = run_researcher(user_query)
    observe_handoff("Researcher", "Analyst", len(research_data))

    # Step 2: Analysis — identify patterns and risk
    observe("COORDINATOR", "Phase 2: Dispatching Analyst")
    analysis = run_analyst(user_query, research_data)
    observe_handoff("Analyst", "Writer", len(analysis))

    # Step 3: Writing — create the report
    observe("COORDINATOR", "Phase 3: Dispatching Writer")
    report = run_writer(user_query, analysis)
    observe_handoff("Writer", "Reviewer", len(report))

    # Step 4: Review — check quality
    observe("COORDINATOR", "Phase 4: Dispatching Reviewer")
    final_report = run_reviewer(user_query, report)

    observe("COORDINATOR", "Pipeline complete")
    return final_report


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("M14 Lab — Multi-Agent Systems (SOLUTION)")
    print("=" * 60)

    # Scenario 1: Single entity
    print("\n\n>>> Scenario 1: Risk analysis report")
    result1 = run_coordinator(
        "Create a risk analysis report for Greenfield Logistics LLC"
    )
    print(f"\nFINAL OUTPUT:\n{result1}")

    # Scenario 2: Comparative
    print("\n\n>>> Scenario 2: Compare two entities")
    result2 = run_coordinator(
        "Research and compare Nextera Holdings and Peachtree Ventures"
    )
    print(f"\nFINAL OUTPUT:\n{result2}")
