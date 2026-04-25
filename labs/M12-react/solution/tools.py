"""
M12 -- ReAct Agent Tools (Complete -- do not modify)
=====================================================
Three research tools for UCC filing investigation:
  1. search_filings   -- find filings by debtor name and/or state
  2. get_filing_details -- get full details for a specific filing number
  3. calculate_risk     -- compute a risk score for a debtor

Each tool returns a dict. The TOOL_DEFINITIONS list provides Claude-compatible
JSON schemas for function calling. The execute_tool() dispatcher maps tool names
to their implementations.
"""

import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "shared"))
from mock_ucc_data import search_filings as _search, get_filing_by_number, ALL_FILINGS


# ---------------------------------------------------------------------------
# Tool 1: search_filings
# ---------------------------------------------------------------------------
def search_filings(debtor_name: str = None, state: str = None) -> dict:
    """
    Search UCC filings by debtor name and/or state.
    Returns a summary list (filing_number, debtor, state, status, date).
    """
    try:
        results = _search(debtor_name=debtor_name, state=state)
        summaries = []
        for f in results:
            summaries.append({
                "filing_number": f["filing_number"],
                "debtor": f["debtor"]["name"],
                "state": f["state"],
                "status": f["status"],
                "filing_date": f["filing_date"],
                "type": f["type"],
            })
        return {
            "success": True,
            "count": len(summaries),
            "results": summaries,
        }
    except Exception as e:
        return {"success": False, "error": str(e), "count": 0, "results": []}


# ---------------------------------------------------------------------------
# Tool 2: get_filing_details
# ---------------------------------------------------------------------------
def get_filing_details(filing_number: str) -> dict:
    """
    Retrieve full details for a specific UCC filing by its filing number.
    """
    try:
        filing = get_filing_by_number(filing_number)
        if filing is None:
            return {
                "success": False,
                "error": f"Filing '{filing_number}' not found",
                "filing": None,
            }
        return {"success": True, "filing": filing}
    except Exception as e:
        return {"success": False, "error": str(e), "filing": None}


# ---------------------------------------------------------------------------
# Tool 3: calculate_risk
# ---------------------------------------------------------------------------
def calculate_risk(debtor_name: str) -> dict:
    """
    Calculate a risk score for a debtor based on their UCC filing history.

    Scoring factors:
      - Each Active filing:      +0.15
      - Blanket lien ("all assets"): +0.20
      - Multi-state filings:     +0.10
      - Multiple secured parties: +0.10
    Score is capped at 1.0.
    """
    try:
        filings = _search(debtor_name=debtor_name)
        if not filings:
            return {
                "success": False,
                "error": f"No filings found for '{debtor_name}'",
                "risk_score": None,
                "risk_level": None,
                "factors": [],
            }

        score = 0.0
        factors = []

        # Factor 1: Active filing count
        active = [f for f in filings if f["status"] == "Active"]
        active_contribution = len(active) * 0.15
        score += active_contribution
        factors.append(f"{len(active)} active filing(s): +{active_contribution:.2f}")

        # Factor 2: Blanket liens
        blanket_keywords = ["all assets", "all accounts", "now owned or hereafter acquired"]
        blanket_count = 0
        for f in filings:
            desc = f.get("collateral_description", "").lower()
            if any(kw in desc for kw in blanket_keywords):
                blanket_count += 1
        if blanket_count > 0:
            blanket_contribution = 0.20
            score += blanket_contribution
            factors.append(f"{blanket_count} blanket lien(s): +{blanket_contribution:.2f}")

        # Factor 3: Multi-state
        states = set(f["state"] for f in filings)
        if len(states) > 1:
            score += 0.10
            factors.append(f"Filings in {len(states)} states: +0.10")

        # Factor 4: Multiple secured parties
        parties = set(f["secured_party"]["name"] for f in filings)
        if len(parties) > 1:
            score += 0.10
            factors.append(f"{len(parties)} distinct secured parties: +0.10")

        score = min(score, 1.0)

        if score >= 0.7:
            level = "HIGH"
        elif score >= 0.4:
            level = "MEDIUM"
        else:
            level = "LOW"

        return {
            "success": True,
            "debtor_name": debtor_name,
            "filings_analyzed": len(filings),
            "risk_score": round(score, 2),
            "risk_level": level,
            "factors": factors,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "risk_score": None,
            "risk_level": None,
            "factors": [],
        }


# ---------------------------------------------------------------------------
# Tool definitions for Claude API (function calling schema)
# ---------------------------------------------------------------------------
TOOL_DEFINITIONS = [
    {
        "name": "search_filings",
        "description": (
            "Search UCC filings by debtor name and/or state. "
            "Returns a summary list of matching filings with filing number, "
            "debtor name, state, status, and filing date."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "debtor_name": {
                    "type": "string",
                    "description": "Name (or partial name) of the debtor to search for",
                },
                "state": {
                    "type": "string",
                    "description": "US state to filter by (e.g. 'New York', 'California')",
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_filing_details",
        "description": (
            "Get the full details of a specific UCC filing by its filing number. "
            "Returns all fields including collateral description, secured party, "
            "and filing office."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "filing_number": {
                    "type": "string",
                    "description": "The UCC filing number (e.g. 'UCC-2024-NY-0012847')",
                },
            },
            "required": ["filing_number"],
        },
    },
    {
        "name": "calculate_risk",
        "description": (
            "Calculate a risk score (0.0-1.0) for a debtor based on their UCC "
            "filing history. Considers number of active filings, blanket liens, "
            "multi-state presence, and number of distinct secured parties. "
            "Returns risk_score, risk_level (LOW/MEDIUM/HIGH), and contributing factors."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "debtor_name": {
                    "type": "string",
                    "description": "Name of the debtor to assess risk for",
                },
            },
            "required": ["debtor_name"],
        },
    },
]


# ---------------------------------------------------------------------------
# Tool dispatcher
# ---------------------------------------------------------------------------
TOOL_MAP = {
    "search_filings": search_filings,
    "get_filing_details": get_filing_details,
    "calculate_risk": calculate_risk,
}


def execute_tool(tool_name: str, tool_input: dict) -> dict:
    """
    Dispatch a tool call by name. Returns the tool's result dict,
    or an error dict if the tool name is unknown.
    """
    if tool_name not in TOOL_MAP:
        return {"success": False, "error": f"Unknown tool: {tool_name}"}
    try:
        return TOOL_MAP[tool_name](**tool_input)
    except TypeError as e:
        return {"success": False, "error": f"Invalid arguments for {tool_name}: {e}"}
    except Exception as e:
        return {"success": False, "error": f"Tool execution error: {e}"}


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("M12 Tools Self-Test")
    print("=" * 40)

    r1 = search_filings(debtor_name="Acme")
    print(f"search_filings('Acme'): {r1['count']} results")

    r2 = search_filings(debtor_name="Greenfield")
    print(f"search_filings('Greenfield'): {r2['count']} results")

    r3 = get_filing_details("UCC-2024-CA-0098231")
    found = "found" if r3["success"] else "NOT FOUND"
    print(f"get_filing_details('UCC-2024-CA-0098231'): {found}")

    r4 = calculate_risk("Greenfield Logistics")
    if r4["success"]:
        print(f"calculate_risk('Greenfield Logistics'): score={r4['risk_score']}, level={r4['risk_level']}")
    else:
        print(f"calculate_risk('Greenfield Logistics'): ERROR - {r4['error']}")

    r5 = execute_tool("search_filings", {"debtor_name": "Pacific"})
    print(f"execute_tool('search_filings', debtor='Pacific'): {r5['count']} results")

    print("=" * 40)
    print("All tools working!")
