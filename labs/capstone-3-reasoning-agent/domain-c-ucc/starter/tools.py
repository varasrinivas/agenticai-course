"""
UCC Entity Resolution Agent — Tool Definitions (Starter)

This file defines:
1. TOOL_SCHEMAS — Anthropic tool schemas sent to the Claude API
2. Tool handler functions — implementations that look up mock data

YOUR TASK: Complete the TODO sections in each tool function.
"""

from mock_data import UCC_FILINGS, BUSINESS_REGISTRY

# ---------------------------------------------------------------------------
# Tool Schemas (Anthropic format)
# ---------------------------------------------------------------------------
TOOL_SCHEMAS = [
    {
        "name": "search_filings_by_name",
        "description": (
            "Search UCC filings across all states for a given business name. "
            "Returns all filings where the debtor name contains or closely matches "
            "the search term. Use this FIRST to discover all filings associated "
            "with a business entity."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "business_name": {
                    "type": "string",
                    "description": "The business name to search for (e.g., 'Acme Corp')",
                },
                "state": {
                    "type": "string",
                    "description": "Optional: limit search to a specific state (e.g., 'CA'). If omitted, searches all states.",
                },
            },
            "required": ["business_name"],
        },
    },
    {
        "name": "fuzzy_match_score",
        "description": (
            "Calculate a fuzzy match confidence score between two business names. "
            "Returns a score from 0.0 to 1.0 and a breakdown of matching factors "
            "(exact match, substring, abbreviation, DBA). Use this to determine "
            "whether two name variations likely refer to the same entity."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "name_a": {
                    "type": "string",
                    "description": "The first business name",
                },
                "name_b": {
                    "type": "string",
                    "description": "The second business name to compare",
                },
            },
            "required": ["name_a", "name_b"],
        },
    },
    {
        "name": "get_filing_details",
        "description": (
            "Get the full details of a specific UCC filing by filing number. "
            "Returns debtor info, secured party, collateral description, status, "
            "and any amendments."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "filing_number": {
                    "type": "string",
                    "description": "The UCC filing number (e.g., 'CA-2023-0847291')",
                },
                "state": {
                    "type": "string",
                    "description": "The state where the filing was made (e.g., 'CA')",
                },
            },
            "required": ["filing_number", "state"],
        },
    },
    {
        "name": "get_business_registry_data",
        "description": (
            "Look up official business registration data by EIN or business name. "
            "Returns legal entity name, DBA names, officers, addresses, entity type, "
            "and name history. Use this to confirm entity identity and find DBAs."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ein": {
                    "type": "string",
                    "description": "The business EIN/Tax ID (e.g., '94-3829471'). Either EIN or business_name is required.",
                },
                "business_name": {
                    "type": "string",
                    "description": "The business name to look up. Either EIN or business_name is required.",
                },
            },
            "required": [],
        },
    },
    {
        "name": "merge_entity_profile",
        "description": (
            "Merge multiple filings and data sources into a unified entity profile. "
            "Provide the confirmed entity details, all associated filings, and risk "
            "assessment. Use this as the FINAL step after resolving entity identity."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "entity_name": {
                    "type": "string",
                    "description": "The confirmed legal entity name",
                },
                "ein": {
                    "type": "string",
                    "description": "The confirmed EIN",
                },
                "name_variations": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "All known name variations for this entity",
                },
                "filing_numbers": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "All UCC filing numbers associated with this entity",
                },
                "states_with_filings": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "States where filings were found",
                },
                "total_secured_parties": {
                    "type": "integer",
                    "description": "Number of distinct secured parties/lenders",
                },
                "risk_notes": {
                    "type": "string",
                    "description": "Any risk observations (e.g., blanket liens, overlapping collateral)",
                },
            },
            "required": [
                "entity_name",
                "ein",
                "name_variations",
                "filing_numbers",
                "states_with_filings",
                "total_secured_parties",
                "risk_notes",
            ],
        },
    },
]


# ---------------------------------------------------------------------------
# Tool Handler Functions — complete the TODOs
# ---------------------------------------------------------------------------

def search_filings_by_name(business_name: str, state: str = None) -> dict:
    """Search UCC filings by business name across states."""
    # TODO:
    # 1. Normalize the business_name to uppercase for comparison
    # 2. Iterate over UCC_FILINGS (all states, or just the specified state)
    # 3. For each filing, check if the normalized debtor_name contains
    #    the normalized search term (case-insensitive substring match)
    # 4. Return a dict with:
    #    - "query": the original business_name
    #    - "results_count": number of matching filings
    #    - "results": list of matching filings (include state, filing_number,
    #      debtor_name, secured_party, filing_date, status)
    pass


def fuzzy_match_score(name_a: str, name_b: str) -> dict:
    """Calculate fuzzy match score between two names."""
    # TODO:
    # Implement a simple fuzzy matching algorithm:
    # 1. Normalize both names (uppercase, strip whitespace)
    # 2. Check for exact match → score 1.0
    # 3. Check if one is a substring of the other → score 0.85
    # 4. Check abbreviation match (e.g., "Corp" vs "Corporation") → score 0.90
    # 5. Check common token overlap → score = (shared tokens / total unique tokens)
    # 6. Return a dict with:
    #    - "name_a": name_a
    #    - "name_b": name_b
    #    - "score": float 0.0 to 1.0
    #    - "match_type": "exact" | "substring" | "abbreviation" | "token_overlap" | "low_match"
    #    - "details": explanation of the match
    pass


def get_filing_details(filing_number: str, state: str) -> dict:
    """Get full details of a specific UCC filing."""
    # TODO:
    # 1. Look up the state in UCC_FILINGS
    # 2. Look up the filing_number within that state
    # 3. Return the full filing dict
    # Handle: state not found, filing not found
    pass


def get_business_registry_data(ein: str = None, business_name: str = None) -> dict:
    """Look up business registration data."""
    # TODO:
    # 1. If ein is provided, look up directly in BUSINESS_REGISTRY
    # 2. If only business_name is provided, search through all entries
    #    checking legal_name and dba_names for a match
    # 3. Return the registry data
    # Handle: not found, neither ein nor name provided
    pass


def merge_entity_profile(
    entity_name: str,
    ein: str,
    name_variations: list,
    filing_numbers: list,
    states_with_filings: list,
    total_secured_parties: int,
    risk_notes: str,
) -> dict:
    """Merge data into a unified entity profile."""
    # TODO:
    # Build a comprehensive entity profile dict with:
    # - "entity_name": confirmed legal name
    # - "ein": confirmed EIN
    # - "name_variations": all known name variations
    # - "filing_summary": {"total_filings": len, "states": list, "active_filings": count}
    # - "lien_exposure": {"total_secured_parties": count, "filing_numbers": list}
    # - "risk_assessment": risk_notes
    # - "profile_status": "resolved"
    # - "confidence_score": calculated based on number of data points
    pass


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------
TOOL_HANDLERS = {
    "search_filings_by_name": lambda args: search_filings_by_name(**args),
    "fuzzy_match_score": lambda args: fuzzy_match_score(**args),
    "get_filing_details": lambda args: get_filing_details(**args),
    "get_business_registry_data": lambda args: get_business_registry_data(**args),
    "merge_entity_profile": lambda args: merge_entity_profile(**args),
}


def execute_tool(tool_name: str, tool_input: dict) -> str:
    """Execute a tool by name and return the result as a JSON string."""
    import json

    handler = TOOL_HANDLERS.get(tool_name)
    if not handler:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})

    try:
        result = handler(tool_input)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Tool execution failed: {str(e)}"})
