"""
M15B — Tools (Solution)
========================
3 complete tools for the UCC Filing Research System.

Usage:
    python tools.py  # runs self-test
"""

import json
from mock_data import search_filings as _search, get_filing_by_number, MOCK_FILINGS


TOOL_DEFINITIONS = [
    {
        "name": "search_filings",
        "description": "Search UCC filings by debtor name and/or state. Returns matching filings with key details.",
        "input_schema": {
            "type": "object",
            "properties": {
                "debtor_name": {"type": "string", "description": "Full or partial debtor name"},
                "state": {"type": "string", "description": "US state (e.g. 'New York', 'Texas')"}
            },
            "required": []
        }
    },
    {
        "name": "get_filing_details",
        "description": "Get complete details of a specific UCC filing by filing number.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filing_number": {"type": "string", "description": "The UCC filing number"}
            },
            "required": ["filing_number"]
        }
    },
    {
        "name": "calculate_risk_score",
        "description": "Calculate lien risk profile for a debtor based on all their UCC filings. Returns risk score, level, factors, and recommendation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "debtor_name": {"type": "string", "description": "Debtor name to assess"}
            },
            "required": ["debtor_name"]
        }
    }
]


def tool_search_filings(debtor_name: str = None, state: str = None) -> str:
    """Search for UCC filings matching criteria."""
    try:
        results = _search(debtor_name=debtor_name, state=state)
        if not results:
            return json.dumps({"message": "No filings found matching the search criteria.",
                               "debtor_name": debtor_name, "state": state})
        summaries = [{
            "filing_number": f["filing_number"],
            "debtor": f["debtor"]["name"],
            "secured_party": f["secured_party"]["name"],
            "state": f["state"],
            "status": f["status"],
            "type": f["type"],
            "filing_date": f["filing_date"],
            "collateral": f["collateral_description"][:120] + "..."
        } for f in results]
        return json.dumps(summaries, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Search failed: {str(e)}"})


def tool_get_filing_details(filing_number: str) -> str:
    """Get full details for a specific filing."""
    try:
        filing = get_filing_by_number(filing_number)
        if filing:
            return json.dumps(filing, indent=2, default=str)
        return json.dumps({"error": f"Filing '{filing_number}' not found.",
                           "hint": "Check the filing number format (e.g. UCC-2024-NY-0012847)"})
    except Exception as e:
        return json.dumps({"error": f"Lookup failed: {str(e)}"})


def tool_calculate_risk_score(debtor_name: str) -> str:
    """Calculate risk profile for a debtor."""
    try:
        filings = _search(debtor_name=debtor_name)
        if not filings:
            return json.dumps({
                "debtor": debtor_name,
                "risk_score": 0,
                "risk_level": "UNKNOWN",
                "message": f"No filings found for '{debtor_name}'. Cannot assess risk."
            })

        active = [f for f in filings if f["status"] == "Active"]
        blanket = [f for f in filings if "all assets" in f["collateral_description"].lower()
                   or "all accounts" in f["collateral_description"].lower()]
        amendments = [f for f in filings if f["type"] == "UCC-3"]
        states = list(set(f["state"] for f in filings))
        secured_parties = list(set(f["secured_party"]["name"] for f in filings))

        # Calculate score
        score = 0.0
        score += len(active) * 0.15
        score += len(blanket) * 0.2
        score += len(amendments) * 0.05
        if len(states) > 1:
            score += 0.1
        if len(secured_parties) > 1:
            score += 0.1
        score = min(1.0, round(score, 2))

        # Determine level and recommendation
        if score >= 0.7:
            level = "HIGH"
            rec = "Significant lien exposure across multiple jurisdictions. Detailed due diligence strongly recommended before extending any credit."
        elif score >= 0.4:
            level = "MEDIUM"
            rec = "Moderate lien activity. Review collateral descriptions and secured party priorities. Consider requesting subordination agreements."
        else:
            level = "LOW"
            rec = "Limited lien exposure. Standard credit evaluation procedures should suffice."

        factors = [
            f"{len(active)} active filing(s) out of {len(filings)} total",
            f"{len(blanket)} blanket lien(s) covering all assets",
            f"{len(amendments)} amendment(s) on file",
            f"Filings across {len(states)} state(s): {', '.join(sorted(states))}",
            f"{len(secured_parties)} distinct secured party/parties: {', '.join(sorted(secured_parties))}",
        ]

        return json.dumps({
            "debtor": debtor_name,
            "risk_score": score,
            "risk_level": level,
            "total_filings": len(filings),
            "active_filings": len(active),
            "blanket_liens": len(blanket),
            "amendments": len(amendments),
            "states": sorted(states),
            "secured_parties": sorted(secured_parties),
            "factors": factors,
            "recommendation": rec,
        }, indent=2)

    except Exception as e:
        return json.dumps({"error": f"Risk calculation failed: {str(e)}"})


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


if __name__ == "__main__":
    print("=" * 60)
    print("M15B — Tools Self-Test (SOLUTION)")
    print("=" * 60)

    print("\n--- search_filings('Acme') ---")
    print(tool_search_filings(debtor_name="Acme"))

    print("\n--- get_filing_details('UCC-2024-NY-0012847') ---")
    print(tool_get_filing_details("UCC-2024-NY-0012847"))

    print("\n--- calculate_risk_score('Acme Corporation') ---")
    print(tool_calculate_risk_score("Acme Corporation"))

    print("\n--- search_filings('NonExistent') ---")
    print(tool_search_filings(debtor_name="NonExistent"))
