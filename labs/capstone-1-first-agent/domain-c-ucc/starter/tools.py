"""
UCC Filing Lookup Agent — Tool Definitions
=============================================
This module defines the tool schema and implementation for the
search_ucc_filings tool.

YOUR TASK: Implement the search_ucc_filings() function body.
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
        filings, or an empty list if no matches found.

    TODO: Implement this function.
    - Iterate over all records in UCC_FILINGS
    - For each record, check if:
      (a) business_name (case-insensitive) appears anywhere in the
          debtor's name, AND
      (b) the record's state matches the provided state (case-insensitive)
    - Return {"results": [list of matching records], "total": count}
    - If no matches, return {"results": [], "total": 0,
                             "message": "No UCC filings found for ..."}
    """
    # TODO: Implement this function
    pass
