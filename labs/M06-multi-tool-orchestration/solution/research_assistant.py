"""
M06 Lab - Step 3: Full Research Assistant with 5 Tools (Solution)
==================================================================
Complete solution: a UCC filing research assistant that orchestrates
5 tools to handle complex multi-step research queries.

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
MODEL = "claude-sonnet-4-20250514"


# =============================================================================
# SHARED MOCK DATA IMPORT
# =============================================================================

# Add the labs directory to the path so we can import shared modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from shared.mock_ucc_data import MOCK_FILINGS, ALL_FILINGS, search_filings, get_filing_by_number


# =============================================================================
# TOOL IMPLEMENTATIONS
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
    score = 20

    filing_factor = min(filing_count * 15, 45)
    score += filing_factor

    collateral_factor = 0
    for ctype in collateral_types:
        ctype_lower = ctype.lower()
        if "blanket" in ctype_lower or "all assets" in ctype_lower:
            collateral_factor += 20
        elif "specific" in ctype_lower:
            collateral_factor += 5
        elif "intellectual property" in ctype_lower:
            collateral_factor += 15
        elif "termination" in ctype_lower:
            collateral_factor -= 10
        else:
            collateral_factor += 10

    score += min(collateral_factor, 35)
    score = max(0, min(100, score))

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
# TOOL DEFINITIONS
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
# TOOL DISPATCHER
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

MAX_TURNS = 15

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
# OBSERVATION HELPERS
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
# SOLUTION: The 5-Tool Agent Loop
# =============================================================================

def run_agent(user_message: str) -> str:
    """
    Run the research assistant agent with 5 tools.

    WHY 5 tools matters: With more tools available, Claude must make smarter
    selection decisions. The agent loop is the same pattern -- what changes
    is the complexity of tool orchestration. Claude may:
    - Call a single tool (simple lookup)
    - Chain 2-3 tools sequentially (search -> details -> summarize)
    - Use parallel calls (search multiple states at once)
    - Mix parallel and sequential in one conversation
    """
    observe("QUERY", user_message)

    # Initialize conversation memory
    messages = [{"role": "user", "content": user_message}]
    total_tool_calls = 0
    tools_used = []  # Track all tools used (with duplicates for chain tracking)

    # === THE AGENT LOOP ===
    turn = 0
    while turn < MAX_TURNS:
        turn += 1
        observe("THINKING", f"Turn {turn} -- sending {len(messages)} message(s) to Claude...")

        # DECIDE: Ask Claude what to do next
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,  # Larger for reports
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        if response.stop_reason == "tool_use":
            # ACT: Execute all tool calls from this turn
            tool_results = []

            for block in response.content:
                if block.type == "tool_use":
                    observe_tool_call(block.name, block.input)

                    # Dispatch to the correct tool function
                    if block.name in TOOL_FUNCTIONS:
                        try:
                            result = TOOL_FUNCTIONS[block.name](block.input)
                        except Exception as e:
                            # Catch tool execution errors and report them back
                            # WHY: Claude can recover from errors if we tell it what happened
                            result = {"error": f"Tool '{block.name}' failed: {str(e)}"}
                    else:
                        # Unknown tool -- should never happen with correct definitions
                        result = {"error": f"Unknown tool: {block.name}"}

                    observe_tool_result(block.name, result)

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result),
                    })

                    # Track usage
                    tools_used.append(block.name)
                    total_tool_calls += 1

            # OBSERVE: Add to conversation memory
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})

        elif response.stop_reason == "end_turn":
            # Claude is done -- extract text
            final_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    final_text += block.text

            # Print usage summary
            unique = sorted(set(tools_used))
            print(f"\n[SUMMARY] {total_tool_calls} tool calls using "
                  f"{len(unique)} unique tools: {', '.join(unique)}")

            observe("RESPONSE", final_text)
            return final_text

        else:
            observe("WARNING", f"Unexpected stop reason: {response.stop_reason}")
            return "Agent stopped unexpectedly."

    observe("ERROR", f"Agent exceeded maximum turns ({MAX_TURNS})")
    return "Error: Agent exceeded maximum number of turns."


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("M06 Lab - Step 3: Full Research Assistant (5 Tools) (SOLUTION)")
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
