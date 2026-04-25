"""
M12 Lab — The ReAct Agent Loop (Starter)
=========================================
Build a ReAct (Reason + Act) research agent that loops over
Claude's tool-use API to answer multi-step UCC filing questions.

KEY CONCEPT: An agent is just a LOOP. Send a message to Claude,
check stop_reason — if it's "tool_use", execute the tool and
send the result back. If it's "end_turn", you're done. That's it.
The magic is in the loop, not in any single API call.

Usage:
    python react_agent.py
"""

import json
import sys
import os
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import anthropic
from shared.mock_ucc_data import search_filings, get_filing_by_number, ALL_FILINGS

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-20250514"


# =============================================================================
# OBSERVATION HELPERS (complete — do not modify)
# These log every step so you can see the Think → Act → Observe trace.
# =============================================================================

def observe(label: str, message: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"[{label}] {message}")
    print(f"{'=' * 60}")


def observe_tool_call(tool_name: str, tool_input: dict) -> None:
    print(f"\n{'─' * 60}")
    print(f"[ACT]   Tool: {tool_name}")
    print(f"[INPUT] {json.dumps(tool_input, indent=2)}")
    print(f"{'─' * 60}")


def observe_tool_result(result: str) -> None:
    print(f"\n{'─' * 60}")
    print(f"[OBSERVE] Tool result:")
    # Truncate long results for readability
    if len(result) > 500:
        print(result[:500] + "\n... (truncated)")
    else:
        print(result)
    print(f"{'─' * 60}")


def observe_thinking(text: str) -> None:
    print(f"\n{'─' * 60}")
    print(f"[THINK] {text[:300]}{'...' if len(text) > 300 else ''}")
    print(f"{'─' * 60}")


# =============================================================================
# TOOL DEFINITIONS
# =============================================================================

# WHAT: Tell Claude what tools are available by describing each one
#   with a name, description, and JSON Schema for its parameters.
# WHY:  Claude reads these schemas to decide which tool to call and
#   what arguments to pass. Good descriptions = better tool selection.
# GOTCHA: The "required" field matters — omit optional params from it
#   or Claude may hallucinate values to satisfy the schema.

TOOLS = [
    {
        "name": "search_filings",
        "description": "Search UCC filings by debtor name and/or state. Returns a list of matching filings with key details. Use this to find filings for a specific company or in a specific state.",
        "input_schema": {
            "type": "object",
            "properties": {
                "debtor_name": {
                    "type": "string",
                    "description": "Full or partial debtor (company) name to search for"
                },
                "state": {
                    "type": "string",
                    "description": "US state to filter results (e.g. 'New York', 'Texas')"
                }
            },
            "required": []
        }
    },
    {
        "name": "get_filing_details",
        "description": "Get the full details of a specific UCC filing by its filing number. Returns all fields including collateral description, dates, and parties.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filing_number": {
                    "type": "string",
                    "description": "The UCC filing number (e.g. 'UCC-2024-NY-0012847')"
                }
            },
            "required": ["filing_number"]
        }
    },
    {
        "name": "calculate_risk",
        "description": "Calculate a risk profile for a debtor based on their UCC filings. Analyzes filing count, collateral breadth, lien types, and expiration proximity to produce a risk score and recommendation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "debtor_name": {
                    "type": "string",
                    "description": "The debtor name to assess risk for"
                }
            },
            "required": ["debtor_name"]
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
        return {
            "debtor": debtor_name,
            "risk_score": 0,
            "risk_level": "UNKNOWN",
            "message": f"No filings found for '{debtor_name}'"
        }

    active = [f for f in filings if f["status"] == "Active"]
    blanket = [f for f in filings if "all assets" in f["collateral_description"].lower()
               or "all accounts" in f["collateral_description"].lower()]
    amendments = [f for f in filings if f["type"] == "UCC-3"]

    # Score: more filings + broader collateral = higher risk
    score = min(1.0, (len(active) * 0.25) + (len(blanket) * 0.3) + (len(amendments) * 0.1))

    if score >= 0.7:
        level = "HIGH"
        rec = "Significant lien exposure. Detailed due diligence recommended before extending credit."
    elif score >= 0.4:
        level = "MEDIUM"
        rec = "Moderate lien activity. Review collateral descriptions and secured party priorities."
    else:
        level = "LOW"
        rec = "Limited lien exposure. Standard credit procedures should suffice."

    return {
        "debtor": debtor_name,
        "risk_score": round(score, 2),
        "risk_level": level,
        "total_filings": len(filings),
        "active_filings": len(active),
        "blanket_liens": len(blanket),
        "amendments": len(amendments),
        "recommendation": rec,
        "factors": [
            f"{len(active)} active filing(s)",
            f"{len(blanket)} blanket lien(s) covering all assets",
            f"{len(amendments)} amendment(s) on file",
        ]
    }


def execute_tool(tool_name: str, tool_input: dict) -> str:
    """Dispatch a tool call to the appropriate function. Returns JSON string."""
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
                "state": f["state"],
                "status": f["status"],
                "type": f["type"],
                "collateral": f["collateral_description"][:120] + "..."
            } for f in results], indent=2)

        elif tool_name == "get_filing_details":
            filing = get_filing_by_number(tool_input["filing_number"])
            if filing:
                return json.dumps(filing, indent=2, default=str)
            return json.dumps({"error": f"Filing {tool_input['filing_number']} not found"})

        elif tool_name == "calculate_risk":
            profile = calculate_risk_for_debtor(tool_input["debtor_name"])
            return json.dumps(profile, indent=2)

        else:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})

    except Exception as e:
        return json.dumps({"error": f"Tool execution failed: {str(e)}"})


# =============================================================================
# SYSTEM PROMPT (complete — do not modify)
# =============================================================================

SYSTEM_PROMPT = """You are a UCC (Uniform Commercial Code) filing research agent.

Your job is to help users research UCC filings — public records that document
secured commercial transactions (liens). You have three tools available:

1. search_filings — find filings by debtor name and/or state
2. get_filing_details — get complete details for a specific filing
3. calculate_risk — assess lien risk for a debtor

## How to Work
- ALWAYS use tools to find information. Never guess or make up filing data.
- When researching a company, start by searching for their filings.
- If asked about risk, use calculate_risk after finding the relevant filings.
- Cite specific filing numbers and data in your answers.
- If no results are found, say so clearly.

## Response Format
- Lead with the key finding
- Include specific filing numbers, dates, and parties
- End with a brief assessment or recommendation if relevant
"""


# =============================================================================
# REACT AGENT LOOP — YOUR CODE HERE
# =============================================================================

def run_react_agent(user_query: str, max_turns: int = 10) -> str:
    """
    Run a ReAct agent loop for the given user query.

    The loop:
    1. Send user query + tools to Claude
    2. Check stop_reason
       - "tool_use" → execute tool(s), send results back, continue loop
       - "end_turn"  → extract text response, return it
    3. Repeat until done or max_turns reached

    Args:
        user_query: The user's question about UCC filings
        max_turns: Safety cap on loop iterations (default 10)

    Returns:
        Claude's final text response
    """
    observe("QUERY", user_query)

    # ------------------------------------------------------------------
    # TODO 1: Initialize the messages list
    #   - Create a list with one entry: {"role": "user", "content": user_query}
    # ------------------------------------------------------------------
    messages = None  # Replace with your code

    # ------------------------------------------------------------------
    # TODO 2: Implement the ReAct loop
    #   - Loop up to max_turns times
    #   - Call client.messages.create() with:
    #       model=MODEL, max_tokens=4096, system=SYSTEM_PROMPT,
    #       tools=TOOLS, messages=messages
    #   - Check response.stop_reason:
    #     a) If NOT "tool_use":
    #        - Extract text from response.content (blocks with .text attr)
    #        - Log it with observe("RESPONSE", ...)
    #        - Return the text
    #     b) If "tool_use":
    #        - Loop through response.content blocks
    #        - For blocks where block.type == "tool_use":
    #          * Log with observe_tool_call(block.name, block.input)
    #          * Execute: result = execute_tool(block.name, block.input)
    #          * Log with observe_tool_result(result)
    #          * Collect tool_result dicts:
    #            {"type": "tool_result", "tool_use_id": block.id, "content": result}
    #        - For blocks where hasattr(block, "text"):
    #          * Log with observe_thinking(block.text)
    #        - Append assistant message: {"role": "assistant", "content": response.content}
    #        - Append user message with tool results: {"role": "user", "content": tool_results}
    #   - After the loop, return a fallback message
    # ------------------------------------------------------------------
    pass


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("M12 Lab — The ReAct Agent Loop")
    print("=" * 60)

    # Query 1: Simple filing search
    print("\n\n>>> Query 1: Find filings for Greenfield Logistics")
    result1 = run_react_agent(
        "Find all UCC filings for Greenfield Logistics in New York"
    )
    print(f"\nFINAL ANSWER:\n{result1}")

    # Query 2: Risk assessment (requires search + calculate)
    print("\n\n>>> Query 2: Risk profile for Nextera Holdings")
    result2 = run_react_agent(
        "What's the risk profile for Nextera Holdings Corp?"
    )
    print(f"\nFINAL ANSWER:\n{result2}")

    # Query 3: State-based search with collateral analysis
    print("\n\n>>> Query 3: Texas filings and collateral")
    result3 = run_react_agent(
        "Search for filings in Texas and tell me about the collateral"
    )
    print(f"\nFINAL ANSWER:\n{result3}")
