"""
M14 Lab — Multi-Agent Systems (Starter)
=========================================
Build a 4-agent content pipeline: researcher, analyst, writer,
reviewer — orchestrated by a coordinator agent.

KEY CONCEPT: Each subagent is a SEPARATE agent with its own
system prompt, tools, and conversation. The coordinator passes
context EXPLICITLY — subagents do NOT inherit the coordinator's
context window. This is the most common mistake in multi-agent
systems: assuming subagents "know" what the coordinator knows.

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
# OBSERVATION HELPERS (complete — do not modify)
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
# TOOL DEFINITIONS (complete — do not modify)
# =============================================================================

RESEARCH_TOOLS = [
    {
        "name": "search_filings",
        "description": "Search UCC filings by debtor name and/or state.",
        "input_schema": {
            "type": "object",
            "properties": {
                "debtor_name": {"type": "string", "description": "Debtor name to search"},
                "state": {"type": "string", "description": "State to filter by"}
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
        "description": "Calculate risk profile for a debtor based on their filings.",
        "input_schema": {
            "type": "object",
            "properties": {
                "debtor_name": {"type": "string", "description": "Debtor name to assess"}
            },
            "required": ["debtor_name"]
        }
    }
]


# =============================================================================
# TOOL EXECUTION (complete — do not modify)
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
# SUBAGENT RUNNER — YOUR CODE HERE
# =============================================================================

def run_subagent(agent_name: str, system_prompt: str, task: str,
                 tools: list = None, max_turns: int = 5) -> str:
    """
    Run a specialist subagent with its own system prompt and tools.

    CRITICAL: This function creates a FRESH conversation for each subagent.
    The subagent does NOT see the coordinator's conversation history.
    Context must be passed EXPLICITLY in the task string.

    Args:
        agent_name: Name for logging (e.g. "Researcher")
        system_prompt: The subagent's role and instructions
        task: The specific task to perform (includes any context from previous agents)
        tools: List of tool definitions (None = no tools, text-only agent)
        max_turns: Max ReAct loop iterations

    Returns:
        The subagent's text response
    """
    observe_agent(agent_name, f"Starting task: {task[:100]}...")

    # ------------------------------------------------------------------
    # TODO 1: Implement run_subagent()
    #   - Create a fresh messages list with the task as user message
    #   - Run a ReAct loop:
    #     a) Call client.messages.create with system_prompt, tools, messages
    #     b) If stop_reason != "tool_use" → extract text, return it
    #     c) If "tool_use" → execute tools, append results, continue
    #   - If tools is None or empty, just make one API call (no loop needed)
    #   - Log completion with observe_agent(agent_name, "Complete")
    #   - Return the text response
    # ------------------------------------------------------------------
    pass


# =============================================================================
# SPECIALIST AGENTS — YOUR CODE HERE
# =============================================================================

def run_researcher(task: str) -> str:
    """
    Research agent — searches for UCC filings and gathers raw data.
    Tools: search_filings, get_filing_details
    """
    # ------------------------------------------------------------------
    # TODO 2: Implement run_researcher()
    #   - Define a system prompt for the researcher role
    #   - Call run_subagent("Researcher", system_prompt, task, RESEARCH_TOOLS)
    #   - Return the result
    # ------------------------------------------------------------------
    pass


def run_analyst(task: str, research_data: str) -> str:
    """
    Analyst agent — analyzes filing data, identifies patterns and risk.
    Tools: calculate_risk
    """
    # ------------------------------------------------------------------
    # TODO 3: Implement run_analyst()
    #   - Define a system prompt for the analyst role
    #   - Include research_data in the task (EXPLICIT context passing)
    #   - Call run_subagent("Analyst", ..., ANALYSIS_TOOLS)
    # ------------------------------------------------------------------
    pass


def run_writer(task: str, analysis: str) -> str:
    """
    Writer agent — generates a report from analysis findings.
    No tools — text generation only.
    """
    # ------------------------------------------------------------------
    # TODO 4: Implement run_writer()
    #   - Define a system prompt for the writer role
    #   - Include analysis data in the task
    #   - Call run_subagent("Writer", ..., tools=None)
    # ------------------------------------------------------------------
    pass


def run_reviewer(task: str, report: str) -> str:
    """
    Reviewer agent — checks report for accuracy and completeness.
    No tools — review only.
    """
    # ------------------------------------------------------------------
    # TODO 5: Implement run_reviewer()
    #   - Define a system prompt for the reviewer role
    #   - Include the report in the task
    #   - Call run_subagent("Reviewer", ..., tools=None)
    # ------------------------------------------------------------------
    pass


# =============================================================================
# COORDINATOR — YOUR CODE HERE
# =============================================================================

def run_coordinator(user_query: str) -> str:
    """
    Coordinator agent — orchestrates the pipeline:
    1. Researcher gathers data
    2. Analyst identifies patterns and risk
    3. Writer creates the report
    4. Reviewer checks quality

    Each agent receives ONLY the context it needs — not the full conversation.
    """
    observe("COORDINATOR", f"Received query: {user_query}")

    # ------------------------------------------------------------------
    # TODO 6: Implement run_coordinator()
    #   Step 1: Call run_researcher(user_query) — get raw filing data
    #   Step 2: Call run_analyst(user_query, research_data) — get analysis
    #           Pass research_data EXPLICITLY
    #   Step 3: Call run_writer(user_query, analysis) — get report draft
    #           Pass analysis EXPLICITLY
    #   Step 4: Call run_reviewer(user_query, report) — get reviewed report
    #           Pass report EXPLICITLY
    #   - Log each handoff with observe_handoff()
    #   - Return the final reviewed report
    #   - Handle errors: if any agent fails, return partial results
    # ------------------------------------------------------------------
    pass


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("M14 Lab — Multi-Agent Systems")
    print("=" * 60)

    # Scenario 1: Single entity analysis
    print("\n\n>>> Scenario 1: Risk analysis report")
    result1 = run_coordinator(
        "Create a risk analysis report for Greenfield Logistics LLC"
    )
    print(f"\nFINAL OUTPUT:\n{result1}")

    # Scenario 2: Comparative analysis
    print("\n\n>>> Scenario 2: Compare two entities")
    result2 = run_coordinator(
        "Research and compare Nextera Holdings and Peachtree Ventures"
    )
    print(f"\nFINAL OUTPUT:\n{result2}")
