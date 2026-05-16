"""
M15B — UCC Tools (SDK Solution)
================================

Same three tools as solution/tools.py, but exposed via @tool +
create_sdk_mcp_server so the Claude Agent SDK can dispatch them.

Tool return shape MUST be {"content": [{"type": "text", "text": ...}]}.
"""
import json
import os
import sys

from claude_agent_sdk import tool, create_sdk_mcp_server

# Reuse the existing mock data + helpers from the manual solution.
HERE = os.path.dirname(os.path.abspath(__file__))
MANUAL_SOLUTION = os.path.normpath(os.path.join(HERE, "..", "solution"))
if MANUAL_SOLUTION not in sys.path:
    sys.path.insert(0, MANUAL_SOLUTION)

from mock_data import search_filings as _search, get_filing_by_number  # noqa: E402


@tool(
    "search_filings",
    "Search UCC filings by debtor name and/or state. Returns a list of filing "
    "summaries (filing_number, debtor, secured_party, state, status, type, "
    "filing_date, collateral). Use partial debtor names freely — matching is "
    "fuzzy. Pass state as the full name e.g. 'New York'.",
    {"debtor_name": str, "state": str},
)
async def sdk_search_filings(args):
    name = args.get("debtor_name")
    state = args.get("state")
    results = _search(debtor_name=name, state=state)
    if not results:
        payload = {"message": "No filings found.", "debtor_name": name, "state": state}
    else:
        payload = [
            {
                "filing_number": f["filing_number"],
                "debtor": f["debtor"]["name"],
                "secured_party": f["secured_party"]["name"],
                "state": f["state"],
                "status": f["status"],
                "type": f["type"],
                "filing_date": f["filing_date"],
                "collateral": f["collateral_description"][:120] + "...",
            }
            for f in results
        ]
    return {"content": [{"type": "text", "text": json.dumps(payload)}]}


@tool(
    "get_filing_details",
    "Get the complete record for a specific UCC filing by filing number "
    "(format UCC-YYYY-ST-NNNNNNN).",
    {"filing_number": str},
)
async def sdk_get_filing_details(args):
    filing = get_filing_by_number(args["filing_number"])
    if filing:
        payload = filing
    else:
        payload = {
            "error": f"Filing '{args['filing_number']}' not found.",
            "hint": "Filing numbers look like UCC-2024-NY-0012847",
        }
    return {"content": [{"type": "text", "text": json.dumps(payload, default=str)}]}


@tool(
    "calculate_risk_score",
    "Compute a lien risk profile for a debtor across all their UCC filings. "
    "Returns risk_score (0-1), risk_level (LOW/MEDIUM/HIGH), contributing "
    "factors, and a recommendation.",
    {"debtor_name": str},
)
async def sdk_calculate_risk_score(args):
    debtor = args["debtor_name"]
    filings = _search(debtor_name=debtor)
    if not filings:
        payload = {
            "debtor": debtor,
            "risk_score": 0,
            "risk_level": "UNKNOWN",
            "message": f"No filings found for '{debtor}' — cannot assess risk.",
        }
        return {"content": [{"type": "text", "text": json.dumps(payload)}]}

    active = [f for f in filings if f["status"] == "Active"]
    blanket = [
        f for f in filings
        if "all assets" in f["collateral_description"].lower()
        or "all accounts" in f["collateral_description"].lower()
    ]
    amendments = [f for f in filings if f["type"] == "UCC-3"]
    states = sorted({f["state"] for f in filings})
    secured_parties = sorted({f["secured_party"]["name"] for f in filings})

    score = (
        len(active) * 0.15
        + len(blanket) * 0.2
        + len(amendments) * 0.05
        + (0.1 if len(states) > 1 else 0)
        + (0.1 if len(secured_parties) > 1 else 0)
    )
    score = round(min(1.0, score), 2)

    if score >= 0.7:
        level, rec = "HIGH", "Significant lien exposure across multiple jurisdictions. Detailed due diligence strongly recommended."
    elif score >= 0.4:
        level, rec = "MEDIUM", "Moderate lien activity. Review collateral descriptions and request subordination where appropriate."
    else:
        level, rec = "LOW", "Limited lien exposure. Standard credit evaluation procedures should suffice."

    payload = {
        "debtor": debtor,
        "risk_score": score,
        "risk_level": level,
        "total_filings": len(filings),
        "active_filings": len(active),
        "blanket_liens": len(blanket),
        "amendments": len(amendments),
        "states": states,
        "secured_parties": secured_parties,
        "factors": [
            f"{len(active)} active filing(s) of {len(filings)} total",
            f"{len(blanket)} blanket lien(s)",
            f"{len(amendments)} amendment(s)",
            f"Filings across {len(states)} state(s): {', '.join(states)}",
            f"{len(secured_parties)} secured party/parties",
        ],
        "recommendation": rec,
    }
    return {"content": [{"type": "text", "text": json.dumps(payload)}]}


ucc_server = create_sdk_mcp_server(
    name="ucc_tools",
    version="1.0.0",
    tools=[sdk_search_filings, sdk_get_filing_details, sdk_calculate_risk_score],
)


ALLOWED_TOOLS = [
    "mcp__ucc__search_filings",
    "mcp__ucc__get_filing_details",
    "mcp__ucc__calculate_risk_score",
]
