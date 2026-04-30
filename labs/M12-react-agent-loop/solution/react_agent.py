"""
M12 Lab — The ReAct Agent Loop (Solution)
==========================================
Complete ReAct agent that loops over Claude's tool-use API
to research UCC filings with full trace logging.

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
MODEL = "claude-sonnet-4-6"


# =============================================================================
# OBSERVATION HELPERS
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
# TOOL EXECUTION
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
# SYSTEM PROMPT
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
# REACT AGENT LOOP — SOLUTION
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
    """
    observe("QUERY", user_query)

    # Initialize conversation with the user's question
    messages = [{"role": "user", "content": user_query}]

    for turn in range(max_turns):
        # Ask Claude — it will either respond with text or request tool calls
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        # STOP CONDITION: Claude is done reasoning and has a final answer
        if response.stop_reason != "tool_use":
            final_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    final_text += block.text
            observe("RESPONSE", final_text[:200] + "..." if len(final_text) > 200 else final_text)
            return final_text

        # CONTINUE: Claude wants to use tools — process each tool_use block
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                observe_tool_call(block.name, block.input)
                result = execute_tool(block.name, block.input)
                observe_tool_result(result)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })
            elif hasattr(block, "text"):
                # Claude's reasoning text before the tool call
                observe_thinking(block.text)

        # Append the assistant's response and tool results to the conversation
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})

    # Safety fallback — should rarely reach here
    return "Agent did not produce a final response within max turns."


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("M12 Lab — The ReAct Agent Loop (SOLUTION)")
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
