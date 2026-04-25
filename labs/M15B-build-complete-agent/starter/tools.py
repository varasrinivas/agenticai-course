"""
M15B — Tools (Starter)
=======================
Define 3 tools for the UCC Filing Research System:
1. search_filings — search by debtor name and/or state
2. get_filing_details — get full details for one filing
3. calculate_risk_score — assess lien risk for a debtor

Each tool needs:
- A Python function that does the work
- A JSON Schema definition (TOOL_DEFINITIONS) for Claude
- Error handling that returns structured error responses

Usage:
    python tools.py  # runs self-test
"""

import json
from mock_data import search_filings as _search, get_filing_by_number, MOCK_FILINGS


# =============================================================================
# TOOL DEFINITIONS — Tell Claude what tools are available
# =============================================================================

TOOL_DEFINITIONS = [
    {
        "name": "search_filings",
        "description": "Search UCC filings by debtor name and/or state. Returns a list of matching filings with key details (filing number, debtor, secured party, state, status, collateral summary).",
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
        "description": "Get complete details of a specific UCC filing by its filing number. Returns all fields including full collateral description, dates, addresses, and amendment history.",
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
        "name": "calculate_risk_score",
        "description": "Calculate a lien risk profile for a debtor based on all their UCC filings. Returns risk score (0-1), risk level (LOW/MEDIUM/HIGH), contributing factors, and a recommendation.",
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
# TOOL FUNCTIONS — YOUR CODE HERE
# =============================================================================

def tool_search_filings(debtor_name: str = None, state: str = None) -> str:
    """
    Search for UCC filings matching the given criteria.

    Returns JSON string with a list of filing summaries.
    Each summary includes: filing_number, debtor, secured_party,
    state, status, type, and collateral (truncated to 120 chars).
    """
    # ------------------------------------------------------------------
    # TODO 1: Implement tool_search_filings
    #   - Call _search(debtor_name=debtor_name, state=state)
    #   - For each result, build a summary dict with:
    #     filing_number, debtor (name), secured_party (name),
    #     state, status, type, collateral (first 120 chars + "...")
    #   - Return json.dumps(summaries, indent=2)
    #   - If no results, return JSON with "message": "No filings found"
    #   - Wrap in try/except, return error JSON on failure
    # ------------------------------------------------------------------
    pass


def tool_get_filing_details(filing_number: str) -> str:
    """
    Get full details for a specific filing.

    Returns JSON string with all filing fields.
    """
    # ------------------------------------------------------------------
    # TODO 2: Implement tool_get_filing_details
    #   - Call get_filing_by_number(filing_number)
    #   - If found, return json.dumps(filing, indent=2, default=str)
    #   - If not found, return error JSON
    #   - Wrap in try/except
    # ------------------------------------------------------------------
    pass


def tool_calculate_risk_score(debtor_name: str) -> str:
    """
    Calculate risk profile for a debtor across all their filings.

    Scoring:
    - Each active filing: +0.15
    - Each blanket lien (collateral contains "all assets" or "all accounts"): +0.2
    - Each amendment: +0.05
    - Multiple states: +0.1
    - Multiple secured parties: +0.1

    Returns JSON with: debtor, risk_score, risk_level, total_filings,
    active_filings, states, secured_parties, factors, recommendation.
    """
    # ------------------------------------------------------------------
    # TODO 3: Implement tool_calculate_risk_score
    #   - Search all filings for this debtor
    #   - Count: active, blanket liens, amendments, unique states, unique secured parties
    #   - Calculate score using the formula above (cap at 1.0)
    #   - Determine level: >= 0.7 HIGH, >= 0.4 MEDIUM, else LOW
    #   - Build recommendation string based on level
    #   - Build factors list (e.g. "5 active filings across 4 states")
    #   - Return JSON with all the fields listed above
    # ------------------------------------------------------------------
    pass


# =============================================================================
# TOOL DISPATCHER (complete — do not modify)
# =============================================================================

def execute_tool(tool_name: str, tool_input: dict) -> str:
    """Route a tool call to the appropriate function."""
    if tool_name == "search_filings":
        return tool_search_filings(
            debtor_name=tool_input.get("debtor_name"),
            state=tool_input.get("state")
        )
    elif tool_name == "get_filing_details":
        return tool_get_filing_details(tool_input["filing_number"])
    elif tool_name == "calculate_risk_score":
        return tool_calculate_risk_score(tool_input["debtor_name"])
    else:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})


# =============================================================================
# SELF-TEST
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("M15B — Tools Self-Test")
    print("=" * 60)

    print("\n--- search_filings('Acme') ---")
    result = tool_search_filings(debtor_name="Acme")
    print(result)

    print("\n--- get_filing_details('UCC-2024-NY-0012847') ---")
    result = tool_get_filing_details("UCC-2024-NY-0012847")
    print(result)

    print("\n--- calculate_risk_score('Acme Corporation') ---")
    result = tool_calculate_risk_score("Acme Corporation")
    print(result)

    print("\n--- search_filings('NonExistent') ---")
    result = tool_search_filings(debtor_name="NonExistent")
    print(result)
