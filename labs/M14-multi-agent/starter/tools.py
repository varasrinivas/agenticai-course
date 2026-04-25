"""
M14 -- Tools (Complete -- do not modify)
========================================
Research tools for the multi-agent pipeline.
Provides search_filings, get_filing_details, and calculate_risk
with full tool schemas for Claude's tool-use API.
"""

import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "shared"))

from mock_ucc_data import search_filings, get_filing_by_number


# =============================================================================
# TOOL SCHEMAS — Claude reads these to decide which tool to call
# =============================================================================

RESEARCH_TOOLS = [
    {
        "name": "search_filings",
        "description": (
            "Search UCC filings by debtor name and/or state. Returns a list of "
            "matching filings with key details. Use this to find filings for a "
            "specific company or in a specific state."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "debtor_name": {
                    "type": "string",
                    "description": "Full or partial debtor (company) name to search for",
                },
                "state": {
                    "type": "string",
                    "description": "US state to filter results (e.g. 'New York', 'Texas')",
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_filing_details",
        "description": (
            "Get the full details of a specific UCC filing by its filing number. "
            "Returns all fields including collateral description, dates, and parties."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "filing_number": {
                    "type": "string",
                    "description": "The UCC filing number (e.g. 'UCC-2024-NY-0012847')",
                }
            },
            "required": ["filing_number"],
        },
    },
]

ANALYSIS_TOOLS = [
    {
        "name": "calculate_risk",
        "description": (
            "Calculate a risk profile for a debtor based on their UCC filings. "
            "Analyzes filing count, collateral breadth, lien types, and expiration "
            "proximity to produce a risk score and recommendation."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "debtor_name": {
                    "type": "string",
                    "description": "The debtor name to assess risk for",
                }
            },
            "required": ["debtor_name"],
        },
    }
]


# =============================================================================
# RISK CALCULATOR
# =============================================================================

def calculate_risk_for_debtor(debtor_name: str) -> dict:
    """Analyze all filings for a debtor and return a risk profile."""
    filings = search_filings(debtor_name=debtor_name)
    if not filings:
        return {
            "debtor": debtor_name,
            "risk_score": 0,
            "risk_level": "UNKNOWN",
            "message": f"No filings found for '{debtor_name}'",
        }

    active = [f for f in filings if f["status"] == "Active"]
    blanket = [
        f
        for f in filings
        if "all assets" in f["collateral_description"].lower()
        or "all accounts" in f["collateral_description"].lower()
    ]
    amendments = [f for f in filings if f["type"] == "UCC-3"]

    # Score: more filings + broader collateral = higher risk
    score = min(
        1.0, (len(active) * 0.25) + (len(blanket) * 0.3) + (len(amendments) * 0.1)
    )

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
        ],
    }


# =============================================================================
# TOOL EXECUTION DISPATCHER
# =============================================================================

def execute_tool(tool_name: str, tool_input: dict) -> str:
    """Dispatch a tool call to the appropriate function. Returns JSON string."""
    try:
        if tool_name == "search_filings":
            results = search_filings(
                debtor_name=tool_input.get("debtor_name"),
                state=tool_input.get("state"),
            )
            return json.dumps(
                [
                    {
                        "filing_number": f["filing_number"],
                        "debtor": f["debtor"]["name"],
                        "secured_party": f["secured_party"]["name"],
                        "state": f["state"],
                        "status": f["status"],
                        "type": f["type"],
                        "filing_date": f["filing_date"],
                        "collateral": f["collateral_description"][:150] + "...",
                    }
                    for f in results
                ],
                indent=2,
            )

        elif tool_name == "get_filing_details":
            filing = get_filing_by_number(tool_input["filing_number"])
            if filing:
                return json.dumps(filing, indent=2, default=str)
            return json.dumps(
                {"error": f"Filing {tool_input['filing_number']} not found"}
            )

        elif tool_name == "calculate_risk":
            profile = calculate_risk_for_debtor(tool_input["debtor_name"])
            return json.dumps(profile, indent=2)

        else:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})

    except Exception as e:
        return json.dumps({"error": f"Tool execution failed: {str(e)}"})


if __name__ == "__main__":
    # Quick smoke test
    print("=== Tool Smoke Test ===")
    print("\nsearch_filings(debtor_name='Greenfield'):")
    print(execute_tool("search_filings", {"debtor_name": "Greenfield"}))
    print("\nget_filing_details('UCC-2024-NY-0012847'):")
    print(execute_tool("get_filing_details", {"filing_number": "UCC-2024-NY-0012847"}))
    print("\ncalculate_risk('Greenfield Logistics'):")
    print(execute_tool("calculate_risk", {"debtor_name": "Greenfield Logistics"}))
