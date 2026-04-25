"""
UCC Entity Resolution Agent — Tool Definitions (Solution)

Complete implementations of all five tools used by the ReAct agent.
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
                    "description": "Optional: limit search to a specific state. If omitted, searches all states.",
                },
            },
            "required": ["business_name"],
        },
    },
    {
        "name": "fuzzy_match_score",
        "description": (
            "Calculate a fuzzy match confidence score between two business names. "
            "Returns a score from 0.0 to 1.0 and a breakdown of matching factors."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "name_a": {"type": "string", "description": "The first business name"},
                "name_b": {"type": "string", "description": "The second business name to compare"},
            },
            "required": ["name_a", "name_b"],
        },
    },
    {
        "name": "get_filing_details",
        "description": (
            "Get the full details of a specific UCC filing by filing number."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "filing_number": {"type": "string", "description": "The UCC filing number"},
                "state": {"type": "string", "description": "The state where the filing was made"},
            },
            "required": ["filing_number", "state"],
        },
    },
    {
        "name": "get_business_registry_data",
        "description": (
            "Look up official business registration data by EIN or business name. "
            "Returns legal entity name, DBA names, officers, addresses, and name history."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ein": {"type": "string", "description": "The business EIN/Tax ID"},
                "business_name": {"type": "string", "description": "The business name to look up"},
            },
            "required": [],
        },
    },
    {
        "name": "merge_entity_profile",
        "description": (
            "Merge multiple filings and data sources into a unified entity profile. "
            "Use this as the FINAL step after resolving entity identity."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "entity_name": {"type": "string", "description": "The confirmed legal entity name"},
                "ein": {"type": "string", "description": "The confirmed EIN"},
                "name_variations": {
                    "type": "array", "items": {"type": "string"},
                    "description": "All known name variations",
                },
                "filing_numbers": {
                    "type": "array", "items": {"type": "string"},
                    "description": "All UCC filing numbers associated with this entity",
                },
                "states_with_filings": {
                    "type": "array", "items": {"type": "string"},
                    "description": "States where filings were found",
                },
                "total_secured_parties": {
                    "type": "integer",
                    "description": "Number of distinct secured parties/lenders",
                },
                "risk_notes": {
                    "type": "string",
                    "description": "Any risk observations",
                },
            },
            "required": [
                "entity_name", "ein", "name_variations", "filing_numbers",
                "states_with_filings", "total_secured_parties", "risk_notes",
            ],
        },
    },
]


# ---------------------------------------------------------------------------
# Tool Handler Functions
# ---------------------------------------------------------------------------

# Common abbreviation mappings for fuzzy matching
ABBREVIATIONS = {
    "corp": "corporation",
    "corporation": "corp",
    "inc": "incorporated",
    "incorporated": "inc",
    "llc": "limited liability company",
    "ltd": "limited",
    "intl": "international",
    "international": "intl",
    "co": "company",
    "company": "co",
    "svcs": "services",
    "services": "svcs",
    "svc": "service",
    "mfg": "manufacturing",
    "manufacturing": "mfg",
}


def _normalize(name: str) -> str:
    """Normalize a name for comparison."""
    return " ".join(name.upper().strip().split())


def _tokenize(name: str) -> set:
    """Tokenize a name into a set of normalized words."""
    # Remove common noise words
    noise = {"DBA", "D/B/A", "THE", "A", "AN", "AND", "&", "OF", "FORMERLY"}
    tokens = set(_normalize(name).split())
    return tokens - noise


def search_filings_by_name(business_name: str, state: str = None) -> dict:
    """Search UCC filings by business name across states."""
    search_term = _normalize(business_name)
    results = []

    states_to_search = [state] if state else UCC_FILINGS.keys()

    for st in states_to_search:
        state_filings = UCC_FILINGS.get(st, {})
        for filing_num, filing in state_filings.items():
            debtor_normalized = _normalize(filing["debtor_name"])
            # Check if search term is contained in debtor name or vice versa
            if search_term in debtor_normalized or debtor_normalized in search_term:
                results.append({
                    "state": filing["state"],
                    "filing_number": filing["filing_number"],
                    "debtor_name": filing["debtor_name"],
                    "debtor_ein": filing.get("debtor_ein", "N/A"),
                    "secured_party": filing["secured_party"],
                    "filing_date": filing["filing_date"],
                    "status": filing["status"],
                    "collateral_summary": filing["collateral_description"][:100] + "...",
                })
            else:
                # Also check token overlap for partial matches
                search_tokens = _tokenize(business_name)
                debtor_tokens = _tokenize(filing["debtor_name"])
                overlap = search_tokens & debtor_tokens
                if len(overlap) >= 1 and len(overlap) / len(search_tokens) >= 0.5:
                    results.append({
                        "state": filing["state"],
                        "filing_number": filing["filing_number"],
                        "debtor_name": filing["debtor_name"],
                        "debtor_ein": filing.get("debtor_ein", "N/A"),
                        "secured_party": filing["secured_party"],
                        "filing_date": filing["filing_date"],
                        "status": filing["status"],
                        "collateral_summary": filing["collateral_description"][:100] + "...",
                        "match_type": "partial_token_match",
                    })

    return {
        "query": business_name,
        "states_searched": list(states_to_search),
        "results_count": len(results),
        "results": results,
    }


def fuzzy_match_score(name_a: str, name_b: str) -> dict:
    """Calculate fuzzy match score between two names."""
    norm_a = _normalize(name_a)
    norm_b = _normalize(name_b)

    # Exact match
    if norm_a == norm_b:
        return {
            "name_a": name_a,
            "name_b": name_b,
            "score": 1.0,
            "match_type": "exact",
            "details": "Names are identical after normalization.",
        }

    # Substring match
    if norm_a in norm_b or norm_b in norm_a:
        return {
            "name_a": name_a,
            "name_b": name_b,
            "score": 0.85,
            "match_type": "substring",
            "details": f"One name is a substring of the other. '{min(name_a, name_b, key=len)}' is contained in '{max(name_a, name_b, key=len)}'.",
        }

    # Abbreviation expansion match
    tokens_a = _normalize(name_a).split()
    tokens_b = _normalize(name_b).split()

    expanded_a = []
    for t in tokens_a:
        expanded_a.append(t)
        if t.lower() in ABBREVIATIONS:
            expanded_a.append(ABBREVIATIONS[t.lower()].upper())

    expanded_b = []
    for t in tokens_b:
        expanded_b.append(t)
        if t.lower() in ABBREVIATIONS:
            expanded_b.append(ABBREVIATIONS[t.lower()].upper())

    if set(expanded_a) & set(tokens_b) == set(tokens_b) or set(expanded_b) & set(tokens_a) == set(tokens_a):
        return {
            "name_a": name_a,
            "name_b": name_b,
            "score": 0.90,
            "match_type": "abbreviation",
            "details": "Names match after expanding common abbreviations (Corp/Corporation, Inc/Incorporated, Intl/International).",
        }

    # Token overlap
    set_a = _tokenize(name_a)
    set_b = _tokenize(name_b)
    if not set_a or not set_b:
        return {
            "name_a": name_a,
            "name_b": name_b,
            "score": 0.0,
            "match_type": "low_match",
            "details": "Insufficient tokens for comparison.",
        }

    shared = set_a & set_b
    total = set_a | set_b
    overlap_score = round(len(shared) / len(total), 2)

    if overlap_score >= 0.6:
        match_type = "token_overlap"
    else:
        match_type = "low_match"

    return {
        "name_a": name_a,
        "name_b": name_b,
        "score": overlap_score,
        "match_type": match_type,
        "details": f"Token overlap: {len(shared)} shared tokens out of {len(total)} total unique tokens. Shared: {sorted(shared)}.",
    }


def get_filing_details(filing_number: str, state: str) -> dict:
    """Get full details of a specific UCC filing."""
    state_filings = UCC_FILINGS.get(state)
    if not state_filings:
        return {"error": f"No filings database found for state {state}"}

    filing = state_filings.get(filing_number)
    if not filing:
        return {"error": f"Filing {filing_number} not found in {state}"}

    return filing


def get_business_registry_data(ein: str = None, business_name: str = None) -> dict:
    """Look up business registration data."""
    if not ein and not business_name:
        return {"error": "Either 'ein' or 'business_name' must be provided"}

    # Look up by EIN
    if ein:
        entry = BUSINESS_REGISTRY.get(ein)
        if entry:
            return entry
        return {"error": f"No business found with EIN {ein}"}

    # Look up by name
    search = _normalize(business_name)
    for entry in BUSINESS_REGISTRY.values():
        if _normalize(entry["legal_name"]) == search:
            return entry
        for dba in entry.get("dba_names", []):
            if _normalize(dba) == search:
                return entry

    return {"error": f"No business found matching name '{business_name}'"}


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
    # Count active filings
    active_count = 0
    for state in states_with_filings:
        state_filings = UCC_FILINGS.get(state, {})
        for fn in filing_numbers:
            filing = state_filings.get(fn)
            if filing and filing.get("status") == "active":
                active_count += 1

    # Determine confidence score
    data_points = len(filing_numbers) + len(name_variations) + len(states_with_filings)
    if data_points >= 10:
        confidence = 0.95
    elif data_points >= 6:
        confidence = 0.85
    else:
        confidence = 0.70

    return {
        "entity_name": entity_name,
        "ein": ein,
        "name_variations": name_variations,
        "filing_summary": {
            "total_filings": len(filing_numbers),
            "active_filings": active_count,
            "states": states_with_filings,
            "filing_numbers": filing_numbers,
        },
        "lien_exposure": {
            "total_secured_parties": total_secured_parties,
            "risk_level": "high" if total_secured_parties >= 5 else "moderate" if total_secured_parties >= 3 else "low",
        },
        "risk_assessment": risk_notes,
        "profile_status": "resolved",
        "confidence_score": confidence,
        "resolution_timestamp": "2024-11-22T14:30:00Z",
    }


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
