"""
UCC Filing Lookup Agent — Tool Definitions (SOLUTION)
=======================================================
Complete implementation of the search_ucc_filings tool.
"""

from mock_data import UCC_FILINGS

# ──────────────────────────────────────────────────────────────
# Tool Schema (Anthropic format)
# ──────────────────────────────────────────────────────────────

TOOLS = [
    {
        "name": "search_ucc_filings",
        "description": (
            "Search for UCC (Uniform Commercial Code) financing statement "
            "filings by business name and state. Returns matching UCC-1 filings "
            "including filing number, status (active, lapsed, terminated), "
            "debtor and secured party information, collateral description, "
            "filing and lapse dates, and any amendments. Supports partial "
            "name matching (case-insensitive). "
            "Use this tool when a user asks about UCC filings, liens, or "
            "security interests for a business."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "business_name": {
                    "type": "string",
                    "description": (
                        "The name of the business (debtor) to search for. "
                        "Supports partial matching — e.g., 'Meridian' will match "
                        "'Meridian Logistics Holdings LLC'."
                    ),
                },
                "state": {
                    "type": "string",
                    "description": (
                        "Two-letter state code where the filing was made "
                        "(e.g., 'DE', 'NY', 'TX'). Use this to narrow results "
                        "to a specific state filing office."
                    ),
                },
            },
            "required": ["business_name", "state"],
        },
    }
]


# ──────────────────────────────────────────────────────────────
# Tool Implementation
# ──────────────────────────────────────────────────────────────

def search_ucc_filings(business_name: str, state: str) -> dict:
    """
    Search UCC filings by business name and state.

    Args:
        business_name: The debtor's business name (partial match supported)
        state: Two-letter state code (e.g., "DE")

    Returns:
        A dictionary with a "results" key containing a list of matching
        filings, and a "total" key with the count.
    """
    # Normalize inputs
    business_name_lower = business_name.strip().lower()
    state_upper = state.strip().upper()

    # Search for matching records
    matches = []
    for filing_number, record in UCC_FILINGS.items():
        debtor_name = record["debtor"]["name"].lower()
        record_state = record["state"].upper()

        if business_name_lower in debtor_name and record_state == state_upper:
            matches.append(record)

    if not matches:
        return {
            "results": [],
            "total": 0,
            "message": (
                f"No UCC filings found for business name '{business_name}' "
                f"in state '{state_upper}'. Try broadening your search with "
                f"a shorter name or checking a different state."
            ),
        }

    return {
        "results": matches,
        "total": len(matches),
    }
