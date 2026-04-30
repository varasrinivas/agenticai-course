"""
M06 Lab - Step 3: Full Research Assistant with 5 Tools (Starter)
=================================================================
Build a complete UCC filing research assistant with 5 tools.
Claude selects the right tools, chains them when needed, and handles
complex multi-step research queries.

Usage:
    python research_assistant.py
"""

import json
import sys
import os
from dotenv import load_dotenv

load_dotenv()

import anthropic

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-6"


# =============================================================================
# SHARED MOCK DATA IMPORT
# =============================================================================

# Add the labs directory to the path so we can import shared modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from shared.mock_ucc_data import MOCK_FILINGS, ALL_FILINGS, search_filings, get_filing_by_number


# =============================================================================
# TOOL IMPLEMENTATIONS (complete -- do not modify)
# =============================================================================

def tool_search_filings(debtor_name: str = None, state: str = None, status: str = None) -> dict:
    """Search UCC filings using the shared mock data."""
    results = search_filings(debtor_name=debtor_name, state=state, status=status)
    # Return a simplified view for Claude (full details available via get_filing_details)
    simplified = []
    for f in results:
        simplified.append({
            "filing_number": f["filing_number"],
            "debtor": f["debtor"]["name"],
            "state": f["state"],
            "status": f["status"],
            "type": f["type"],
            "filing_date": f["filing_date"],
        })
    return {"results": simplified, "count": len(simplified)}


def tool_get_filing_details(filing_number: str) -> dict:
    """Get full details for a specific filing."""
    filing = get_filing_by_number(filing_number)
    if filing is None:
        return {"error": f"Filing '{filing_number}' not found."}
    return filing


def tool_summarize_text(text: str) -> dict:
    """Summarize a collateral description into plain English."""
    summary_parts = []
    text_lower = text.lower()

    if "all assets" in text_lower or "blanket lien" in text_lower:
        summary_parts.append("BLANKET LIEN covering essentially all business assets.")
    if "accounts receivable" in text_lower:
        summary_parts.append("Covers receivables (money owed to the company).")
    if "inventory" in text_lower:
        summary_parts.append("Covers physical inventory.")
    if "equipment" in text_lower:
        summary_parts.append("Covers equipment and machinery.")
    if "intellectual property" in text_lower or "patents" in text_lower:
        summary_parts.append("Covers intellectual property (patents, trademarks).")
    if "specific equipment" in text_lower:
        summary_parts.append("SPECIFIC EQUIPMENT lien (not blanket).")
    if "termination" in text_lower:
        summary_parts.append("TERMINATION notice -- lien released.")
    if "general intangibles" in text_lower:
        summary_parts.append("Covers intangible assets.")
    if "farm products" in text_lower or "crops" in text_lower:
        summary_parts.append("Covers farm products and agricultural assets.")
    if "medical equipment" in text_lower:
        summary_parts.append("Covers medical equipment (MRI, CT scanner, etc.).")

    if not summary_parts:
        summary_parts.append("Standard collateral description.")

    return {
        "original_length": len(text),
        "summary": " ".join(summary_parts),
    }


def tool_calculate_risk_score(debtor_name: str, filing_count: int, collateral_types: list) -> dict:
    """
    Calculate a simple lien risk score (0-100) based on:
    - Number of filings (more filings = higher risk)
    - Types of collateral (blanket liens are riskier than specific equipment)
    """
    # Base score starts at 20
    score = 20

    # Filing count factor: each filing adds 15 points (capped contribution at 45)
    filing_factor = min(filing_count * 15, 45)
    score += filing_factor

    # Collateral type factor
    collateral_factor = 0
    for ctype in collateral_types:
        ctype_lower = ctype.lower()
        if "blanket" in ctype_lower or "all assets" in ctype_lower:
            collateral_factor += 20  # Blanket liens are high risk
        elif "specific" in ctype_lower:
            collateral_factor += 5   # Specific equipment is low risk
        elif "intellectual property" in ctype_lower:
            collateral_factor += 15  # IP liens are medium-high risk
        elif "termination" in ctype_lower:
            collateral_factor -= 10  # Terminated filings reduce risk
        else:
            collateral_factor += 10  # Default medium risk

    score += min(collateral_factor, 35)  # Cap collateral contribution

    # Clamp to 0-100
    score = max(0, min(100, score))

    # Risk level label
    if score >= 75:
        level = "High"
    elif score >= 50:
        level = "Moderate"
    elif score >= 25:
        level = "Low"
    else:
        level = "Minimal"

    return {
        "debtor_name": debtor_name,
        "risk_score": score,
        "risk_level": level,
        "factors": {
            "filing_count": filing_count,
            "filing_factor": filing_factor,
            "collateral_types": collateral_types,
            "collateral_factor": min(collateral_factor, 35),
        },
    }


def tool_generate_report(title: str, filings: list, summary: str = None) -> dict:
    """Generate a formatted text report from filing data."""
    lines = []
    lines.append("=" * 50)
    lines.append(f"  UCC FILING REPORT: {title}")
    lines.append("=" * 50)
    lines.append(f"Total Filings: {len(filings)}")
    lines.append("")

    for i, filing in enumerate(filings, 1):
        lines.append(f"--- Filing {i} ---")
        # Handle both full filing objects and simplified objects
        if isinstance(filing, dict):
            for key, value in filing.items():
                if isinstance(value, dict):
                    lines.append(f"  {key}:")
                    for k, v in value.items():
                        lines.append(f"    {k}: {v}")
                else:
                    lines.append(f"  {key}: {value}")
        lines.append("")

    if summary:
        lines.append("--- Summary ---")
        lines.append(summary)
        lines.append("")

    lines.append("=" * 50)
    lines.append("  END OF REPORT")
    lines.append("=" * 50)

    report_text = "\n".join(lines)
    return {
        "report": report_text,
        "filing_count": len(filings),
        "report_length": len(report_text),
    }


# =============================================================================
# TOOL DEFINITIONS (complete -- do not modify)
# =============================================================================

TOOLS = [
    {
        "name": "search_filings",
        "description": (
            "Search UCC filings by debtor name, state, and/or status. "
            "Returns a simplified list of matching filings with filing number, "
            "debtor name, state, status, type, and filing date."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "debtor_name": {
                    "type": "string",
                    "description": "Partial or full debtor name to search for",
                },
                "state": {
                    "type": "string",
                    "description": "State to filter by, e.g. 'New York', 'Texas'",
                },
                "status": {
                    "type": "string",
                    "description": "Filing status: 'Active', 'Terminated', 'Lapsed', 'Amendment'",
                },
            },
        },
    },
    {
        "name": "get_filing_details",
        "description": (
            "Get full details for a specific UCC filing by its filing number. "
            "Returns complete information including debtor address, secured party, "
            "collateral description, filing dates, and document numbers."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "filing_number": {
                    "type": "string",
                    "description": "The UCC filing number, e.g. 'UCC-2024-NY-0012847'",
                }
            },
            "required": ["filing_number"],
        },
    },
    {
        "name": "summarize_text",
        "description": (
            "Summarize a collateral description into plain English. "
            "Identifies the type of lien (blanket vs specific), key asset categories, "
            "and any special conditions (termination, amendment, etc.)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The collateral description text to summarize",
                }
            },
            "required": ["text"],
        },
    },
    {
        "name": "calculate_risk_score",
        "description": (
            "Calculate a lien risk score (0-100) for a debtor based on their "
            "filing count and collateral types. Returns score, risk level "
            "(Minimal/Low/Moderate/High), and contributing factors."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "debtor_name": {
                    "type": "string",
                    "description": "The debtor's name",
                },
                "filing_count": {
                    "type": "integer",
                    "description": "Number of active filings for this debtor",
                },
                "collateral_types": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "List of collateral type descriptions, e.g. "
                        "['blanket lien', 'specific equipment']"
                    ),
                },
            },
            "required": ["debtor_name", "filing_count", "collateral_types"],
        },
    },
    {
        "name": "generate_report",
        "description": (
            "Generate a formatted text report from filing data. "
            "Takes a title, list of filing objects, and optional summary text."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Report title, e.g. 'Filings in Texas'",
                },
                "filings": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "List of filing objects to include in the report",
                },
                "summary": {
                    "type": "string",
                    "description": "Optional summary text to include at the end of the report",
                },
            },
            "required": ["title", "filings"],
        },
    },
]

# =============================================================================
# TOOL DISPATCHER (complete -- do not modify)
# =============================================================================

TOOL_FUNCTIONS = {
    "search_filings": lambda args: tool_search_filings(
        debtor_name=args.get("debtor_name"),
        state=args.get("state"),
        status=args.get("status"),
    ),
    "get_filing_details": lambda args: tool_get_filing_details(args["filing_number"]),
    "summarize_text": lambda args: tool_summarize_text(args["text"]),
    "calculate_risk_score": lambda args: tool_calculate_risk_score(
        debtor_name=args["debtor_name"],
        filing_count=args["filing_count"],
        collateral_types=args["collateral_types"],
    ),
    "generate_report": lambda args: tool_generate_report(
        title=args["title"],
        filings=args["filings"],
        summary=args.get("summary"),
    ),
}

MAX_TURNS = 15  # More turns for complex multi-tool research

SYSTEM_PROMPT = """\
You are a UCC filing research assistant with access to 5 tools:

1. search_filings: Search for UCC filings by debtor name, state, or status
2. get_filing_details: Get complete details for a specific filing number
3. summarize_text: Summarize collateral descriptions into plain English
4. calculate_risk_score: Calculate lien risk score based on filing count and collateral types
5. generate_report: Generate a formatted report from filing data

RESEARCH WORKFLOW:
- Start by searching for relevant filings
- Get details for specific filings when needed
- Summarize collateral in plain English when asked
- Calculate risk scores when evaluating a debtor's lien exposure
- Generate reports when asked for formatted output

Always explain your findings clearly. When you use multiple tools, explain
how the information from each step connects to your final answer.
"""


# =============================================================================
# OBSERVATION HELPERS (complete -- do not modify)
# =============================================================================

def observe(label: str, message: str) -> None:
    """Print a labeled observation line."""
    print(f"\n{'=' * 60}")
    print(f"[{label}] {message}")
    print(f"{'=' * 60}")


def observe_tool_call(tool_name: str, tool_input: dict) -> None:
    """Log a tool call."""
    input_str = json.dumps(tool_input, indent=2)
    if len(input_str) > 300:
        input_str = input_str[:300] + "\n  ... (truncated)"
    print(f"\n{'─' * 60}")
    print(f"[USING TOOL] {tool_name}")
    print(f"[INPUT]      {input_str}")
    print(f"{'─' * 60}")


def observe_tool_result(tool_name: str, result: dict) -> None:
    """Log a tool result."""
    result_str = json.dumps(result, indent=2)
    if len(result_str) > 500:
        result_str = result_str[:500] + "\n  ... (truncated)"
    print(f"\n{'─' * 60}")
    print(f"[TOOL RESULT] {tool_name}")
    print(result_str)
    print(f"{'─' * 60}")


# =============================================================================
# YOUR CODE: Implement the 5-tool agent loop with dispatcher
# =============================================================================

def run_agent(user_message: str) -> str:
    """
    Run the research assistant agent with 5 tools.

    The agent loop is the same pattern as Steps 1 and 2 -- the key difference
    is the SCALE: 5 tools means Claude must choose the right tool(s) for each
    query, and complex queries may require 3-4 tools across multiple turns.

    Returns Claude's final text response.
    """
    observe("QUERY", user_message)

    # ------------------------------------------------------------------
    # TODO 1: Initialize messages and tracking
    #   messages = [{"role": "user", "content": user_message}]
    #   total_tool_calls = 0
    #   tools_used = []  # Track unique tools used
    # ------------------------------------------------------------------
    messages = [{"role": "user", "content": user_message}]
    total_tool_calls = 0
    tools_used = []

    turn = 0
    while turn < MAX_TURNS:
        turn += 1
        observe("THINKING", f"Turn {turn} -- sending {len(messages)} message(s) to Claude...")

        # --------------------------------------------------------------
        # TODO 2: Call the Claude API with all 5 tools
        #   response = client.messages.create(
        #       model=MODEL, max_tokens=4096, system=SYSTEM_PROMPT,
        #       tools=TOOLS, messages=messages,
        #   )
        # --------------------------------------------------------------
        pass

        # --------------------------------------------------------------
        # TODO 3: Handle stop_reason == "tool_use"
        #   For each tool_use block in response.content:
        #     - Log with observe_tool_call
        #     - Look up the tool in TOOL_FUNCTIONS
        #     - If found: execute it (wrap in try/except)
        #     - If not found: return {"error": f"Unknown tool: {name}"}
        #     - Log with observe_tool_result
        #     - Collect tool_result objects
        #     - Track the tool name in tools_used
        #   After processing all blocks:
        #     - Append assistant message to messages
        #     - Append tool results to messages
        #     - Update total_tool_calls
        # --------------------------------------------------------------
        pass

        # --------------------------------------------------------------
        # TODO 4: Handle stop_reason == "end_turn"
        #   - Extract final text from response.content
        #   - Print summary:
        #     unique = sorted(set(tools_used))
        #     print(f"\n[SUMMARY] {total_tool_calls} tool calls using "
        #           f"{len(unique)} unique tools: {', '.join(unique)}")
        #   - observe("RESPONSE", final_text)
        #   - Return final_text
        # --------------------------------------------------------------
        pass

    observe("ERROR", f"Agent exceeded maximum turns ({MAX_TURNS})")
    return "Error: Agent exceeded maximum number of turns."


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("M06 Lab - Step 3: Full Research Assistant (5 Tools)")
    print("=" * 60)

    # Test 1: Search + summarize
    print("\n\n>>> Test 1: Search + summarize")
    result1 = run_agent("Find all active filings in New York and summarize their collateral")
    print(f"\nFINAL ANSWER: {result1}")

    # Test 2: Search + risk score
    print("\n\n>>> Test 2: Search + risk score")
    result2 = run_agent("What's the risk score for Greenfield Logistics LLC?")
    print(f"\nFINAL ANSWER: {result2}")

    # Test 3: Search + details + report
    print("\n\n>>> Test 3: Search + details + report")
    result3 = run_agent("Generate a report on all filings in Texas")
    print(f"\nFINAL ANSWER: {result3}")
