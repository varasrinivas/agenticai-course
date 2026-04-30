"""
M06 Lab - Step 2: Sequential Tool Chain (Solution)
====================================================
Complete solution: multi-turn tool chaining where the output of one tool
feeds into Claude's decision to call the next tool.

Usage:
    python tool_chain.py
"""

import json
from dotenv import load_dotenv

load_dotenv()

import anthropic

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-6"


# =============================================================================
# INLINE MOCK DATA
# =============================================================================

MOCK_FILINGS_DB = [
    {
        "filing_number": "UCC-2024-001",
        "debtor": "Greenfield Logistics LLC",
        "state": "New York",
        "status": "Active",
        "collateral_summary": "All accounts receivable, inventory, equipment, and general intangibles now owned or hereafter acquired by Debtor.",
    },
    {
        "filing_number": "UCC-2024-002",
        "debtor": "Pacific Ridge Technologies Inc",
        "state": "California",
        "status": "Active",
        "collateral_summary": "All assets of the Debtor including but not limited to: intellectual property, patents, trademarks, accounts, deposit accounts, investment property, and all proceeds thereof.",
    },
    {
        "filing_number": "UCC-2023-003",
        "debtor": "Lone Star Energy Solutions LP",
        "state": "Texas",
        "status": "Active",
        "collateral_summary": "Specific equipment: (3) Caterpillar 349F L hydraulic excavators, serial numbers CAT349F-8821, CAT349F-8822, CAT349F-8823; (1) Liebherr LTM 1300-6.2 mobile crane, serial number LTM-DE-90124.",
    },
    {
        "filing_number": "UCC-2024-004",
        "debtor": "Harbor Shipping International Inc",
        "state": "New York",
        "status": "Terminated",
        "collateral_summary": "TERMINATION -- This filing terminates the effectiveness of the original filing.",
    },
]

MOCK_FILING_DETAILS = {
    "UCC-2024-001": {
        "filing_number": "UCC-2024-001",
        "type": "UCC-1",
        "debtor": "Greenfield Logistics LLC",
        "debtor_address": "450 West 33rd Street, Suite 800, New York, NY 10001",
        "secured_party": "Atlantic Capital Partners",
        "state": "New York",
        "filing_date": "2024-03-15",
        "expiration_date": "2029-03-15",
        "status": "Active",
        "collateral_description": "All accounts receivable, inventory, equipment, and general intangibles now owned or hereafter acquired by Debtor. This is a blanket lien covering all present and future assets used in the ordinary course of business.",
    },
    "UCC-2024-002": {
        "filing_number": "UCC-2024-002",
        "type": "UCC-1",
        "debtor": "Pacific Ridge Technologies Inc",
        "debtor_address": "2800 Sand Hill Road, Menlo Park, CA 94025",
        "secured_party": "Silicon Valley Bank",
        "state": "California",
        "filing_date": "2024-01-22",
        "expiration_date": "2029-01-22",
        "status": "Active",
        "collateral_description": "All assets of the Debtor including but not limited to: intellectual property, patents, trademarks, accounts, deposit accounts, investment property, and all proceeds thereof. This filing represents a comprehensive security interest in all tangible and intangible assets.",
    },
    "UCC-2023-003": {
        "filing_number": "UCC-2023-003",
        "type": "UCC-1",
        "debtor": "Lone Star Energy Solutions LP",
        "debtor_address": "1200 Smith Street, Suite 3000, Houston, TX 77002",
        "secured_party": "Wells Fargo Equipment Finance",
        "state": "Texas",
        "filing_date": "2023-09-10",
        "expiration_date": "2028-09-10",
        "status": "Active",
        "collateral_description": "Specific equipment: (3) Caterpillar 349F L hydraulic excavators, serial numbers CAT349F-8821, CAT349F-8822, CAT349F-8823; (1) Liebherr LTM 1300-6.2 mobile crane, serial number LTM-DE-90124. This is a purchase money security interest (PMSI) in specific identified equipment.",
    },
    "UCC-2024-004": {
        "filing_number": "UCC-2024-004",
        "type": "UCC-3",
        "debtor": "Harbor Shipping International Inc",
        "debtor_address": "One World Trade Center, Floor 72, New York, NY 10007",
        "secured_party": "Citibank N.A.",
        "state": "New York",
        "filing_date": "2023-12-01",
        "expiration_date": None,
        "status": "Terminated",
        "collateral_description": "TERMINATION -- This filing terminates the effectiveness of the original filing UCC-2019-NY-0089012. All collateral previously encumbered is now released.",
    },
}


# =============================================================================
# TOOL FUNCTIONS
# =============================================================================

def search_filings(debtor_name: str = None, state: str = None, status: str = None) -> dict:
    """Search mock filings by debtor name, state, and/or status."""
    results = MOCK_FILINGS_DB
    if debtor_name:
        results = [f for f in results if debtor_name.lower() in f["debtor"].lower()]
    if state:
        results = [f for f in results if f["state"].lower() == state.lower()]
    if status:
        results = [f for f in results if f["status"].lower() == status.lower()]

    if not results:
        return {"results": [], "count": 0, "message": "No filings found matching your criteria."}
    return {"results": results, "count": len(results)}


def get_filing_details(filing_number: str) -> dict:
    """Get full details for a specific filing number."""
    if filing_number in MOCK_FILING_DETAILS:
        return MOCK_FILING_DETAILS[filing_number]
    return {"error": f"Filing '{filing_number}' not found. Available: {', '.join(MOCK_FILING_DETAILS.keys())}"}


def summarize_text(text: str) -> dict:
    """Summarize a collateral description into plain English (mock summarizer)."""
    summary_parts = []

    text_lower = text.lower()
    if "all assets" in text_lower or "blanket lien" in text_lower:
        summary_parts.append("This is a BLANKET LIEN covering essentially all business assets.")
    if "accounts receivable" in text_lower:
        summary_parts.append("Covers money owed to the company (receivables).")
    if "inventory" in text_lower:
        summary_parts.append("Covers physical inventory and stock.")
    if "equipment" in text_lower:
        summary_parts.append("Covers business equipment and machinery.")
    if "intellectual property" in text_lower or "patents" in text_lower:
        summary_parts.append("Covers intellectual property (patents, trademarks, etc.).")
    if "specific equipment" in text_lower:
        summary_parts.append("Covers SPECIFIC identified equipment (not a blanket lien).")
    if "termination" in text_lower:
        summary_parts.append("This is a TERMINATION notice -- the original lien has been released.")
    if "general intangibles" in text_lower:
        summary_parts.append("Covers intangible assets (contracts, goodwill, etc.).")

    if not summary_parts:
        summary_parts.append("Standard collateral description -- review full text for details.")

    return {
        "original_length": len(text),
        "summary": " ".join(summary_parts),
    }


# =============================================================================
# TOOL DEFINITIONS
# =============================================================================

TOOLS = [
    {
        "name": "search_filings",
        "description": (
            "Search UCC filings by debtor name, state, and/or status. "
            "Returns a list of matching filings with basic info."
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
                    "description": "Filing status: 'Active', 'Terminated', 'Lapsed'",
                },
            },
        },
    },
    {
        "name": "get_filing_details",
        "description": (
            "Get full details for a specific UCC filing by its filing number. "
            "Returns debtor info, secured party, collateral description, dates, etc."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "filing_number": {
                    "type": "string",
                    "description": "The UCC filing number, e.g. 'UCC-2024-001'",
                }
            },
            "required": ["filing_number"],
        },
    },
    {
        "name": "summarize_text",
        "description": (
            "Summarize a collateral description into plain English. "
            "Identifies the type of lien (blanket vs specific) and key asset categories."
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
]

TOOL_FUNCTIONS = {
    "search_filings": lambda args: search_filings(
        debtor_name=args.get("debtor_name"),
        state=args.get("state"),
        status=args.get("status"),
    ),
    "get_filing_details": lambda args: get_filing_details(args["filing_number"]),
    "summarize_text": lambda args: summarize_text(args["text"]),
}

MAX_TURNS = 10

SYSTEM_PROMPT = """\
You are a UCC filing research assistant with access to three tools:
- search_filings: search for UCC filings by debtor name, state, or status
- get_filing_details: get full details for a specific filing number
- summarize_text: summarize a collateral description into plain English

When researching a filing, follow the natural chain:
1. Search for the filing first
2. Get detailed information using the filing number from search results
3. Summarize the collateral description if the user wants plain English

Always explain your findings clearly after gathering the information.
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
    print(f"\n{'─' * 60}")
    print(f"[USING TOOL] {tool_name}")
    print(f"[INPUT]      {json.dumps(tool_input, indent=2)}")
    print(f"{'─' * 60}")


def observe_tool_result(result: dict) -> None:
    """Log a tool result."""
    result_str = json.dumps(result, indent=2)
    if len(result_str) > 500:
        result_str = result_str[:500] + "\n  ... (truncated)"
    print(f"\n{'─' * 60}")
    print(f"[TOOL RESULT]")
    print(result_str)
    print(f"{'─' * 60}")


# =============================================================================
# SOLUTION: The Chaining-Aware Agent Loop
# =============================================================================

def run_agent(user_message: str) -> str:
    """
    Run the agent loop that supports multi-turn tool chaining.

    WHY chaining matters: Real research tasks require multiple steps.
    A UCC filing search -> detail lookup -> collateral summary is a
    natural 3-step chain. Claude drives the chain by examining each
    tool's output and deciding what to call next.

    The loop is the SAME as M05's agent loop -- the chain pattern
    emerges naturally from Claude's reasoning, not from special code.
    """
    observe("QUERY", user_message)

    # Initialize conversation memory
    messages = [{"role": "user", "content": user_message}]
    total_tool_calls = 0
    chain_steps = []  # Track which tools were called in order

    # === THE AGENT LOOP (same pattern as M05) ===
    turn = 0
    while turn < MAX_TURNS:
        turn += 1
        observe("THINKING", f"Turn {turn} -- sending {len(messages)} message(s) to Claude...")

        # DECIDE: Ask Claude what to do next
        response = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        if response.stop_reason == "tool_use":
            # ACT: Execute tool calls and track the chain
            tool_results = []

            for block in response.content:
                if block.type == "tool_use":
                    observe_tool_call(block.name, block.input)

                    # Execute the tool with error handling
                    if block.name in TOOL_FUNCTIONS:
                        try:
                            result = TOOL_FUNCTIONS[block.name](block.input)
                        except Exception as e:
                            result = {"error": f"Tool execution failed: {str(e)}"}
                    else:
                        result = {"error": f"Unknown tool: {block.name}"}

                    observe_tool_result(result)

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result),
                    })

                    # Track the chain: record which tool was called
                    chain_steps.append(block.name)
                    total_tool_calls += 1

            # OBSERVE: Add messages to memory so Claude can see results
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})

            # REPEAT: Claude will see tool results and decide next step

        elif response.stop_reason == "end_turn":
            # Claude is done -- extract final text
            final_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    final_text += block.text

            # Print chain summary -- shows the tool sequence
            chain_str = " -> ".join(chain_steps) if chain_steps else "(no tools)"
            print(f"\n[CHAIN] Total tool calls: {total_tool_calls} "
                  f"across {turn} turns ({chain_str})")

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
    print("M06 Lab - Step 2: Sequential Tool Chain (SOLUTION)")
    print("=" * 60)

    # Test 1: Full 3-step chain (search -> details -> summarize)
    print("\n\n>>> Test 1: Full 3-step chain")
    result1 = run_agent("Find filings for Greenfield Logistics and summarize the collateral")
    print(f"\nFINAL ANSWER: {result1}")

    # Test 2: 2-step chain (details -> summarize)
    print("\n\n>>> Test 2: 2-step chain")
    result2 = run_agent("Get details on filing UCC-2024-001 and summarize it")
    print(f"\nFINAL ANSWER: {result2}")

    # Test 3: Single tool, no chain
    print("\n\n>>> Test 3: Single tool, no chain")
    result3 = run_agent("Search for filings in New York")
    print(f"\nFINAL ANSWER: {result3}")
