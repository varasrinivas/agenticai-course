"""
M16: Schema Validator — Starter
Validates that user inputs match expected UCC data formats.
"""
import re
import json
from typing import Optional


# ── Validation Rules ─────────────────────────────────────────

# Valid US state codes
VALID_STATES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
    "DC",
}

# UCC filing number format: UCC-YYYY-SS-NNNNNNN
FILING_NUMBER_PATTERN = r"^UCC-\d{4}-[A-Z]{2}-\d{7}$"


def validate_filing_number(filing_number: str) -> dict:
    """
    Validate a UCC filing number format.

    Expected format: UCC-YYYY-SS-NNNNNNN
    - YYYY: 4-digit year (2000-2030)
    - SS: 2-letter state code
    - NNNNNNN: 7-digit sequence number

    Returns:
        {"valid": bool, "errors": [str], "parsed": {year, state, sequence} | None}
    """
    errors = []
    parsed = None

    # TODO 1: Check basic format with regex
    # If doesn't match FILING_NUMBER_PATTERN, add error and return early

    # TODO 2: Extract and validate components
    # Split on "-" to get parts: ["UCC", "YYYY", "SS", "NNNNNNN"]
    # Validate year is between 2000-2030
    # Validate state code is in VALID_STATES
    # Build parsed dict with year (int), state (str), sequence (str)

    return {"valid": len(errors) == 0, "errors": errors, "parsed": parsed}


def validate_search_query(query: dict) -> dict:
    """
    Validate a UCC search query object.

    Expected fields:
        - debtor_name: str, 2-100 chars, no special injection chars
        - state: str, valid 2-letter state code (optional)
        - filing_type: str, one of "UCC-1", "UCC-3" (optional)
        - status: str, one of "Active", "Terminated", "Lapsed", "Amendment" (optional)

    Returns:
        {"valid": bool, "errors": [str], "sanitized": dict}
    """
    errors = []
    sanitized = {}

    # TODO 3: Validate debtor_name
    # - Must be present and non-empty
    # - Must be 2-100 characters
    # - Must not contain SQL injection chars: ;, --, ', ", DROP, DELETE, SELECT
    # - Strip leading/trailing whitespace

    # TODO 4: Validate state (if provided)
    # - Must be 2 uppercase letters
    # - Must be in VALID_STATES

    # TODO 5: Validate filing_type (if provided)
    # - Must be one of: "UCC-1", "UCC-3"

    # TODO 6: Validate status (if provided)
    # - Must be one of: "Active", "Terminated", "Lapsed", "Amendment"

    return {"valid": len(errors) == 0, "errors": errors, "sanitized": sanitized}


# ── Self-Test ────────────────────────────────────────────────
if __name__ == "__main__":
    # Filing number tests
    filing_tests = [
        "UCC-2024-NY-0012847",   # Valid
        "UCC-2024-ZZ-0012847",   # Invalid state
        "UCC-1999-NY-0012847",   # Invalid year
        "ucc-2024-ny-0012847",   # Wrong case
        "RANDOM-STRING",          # Wrong format
        "UCC-2024-NY-12847",     # Wrong sequence length
    ]

    print("=== Filing Number Validation ===")
    for fn in filing_tests:
        result = validate_filing_number(fn)
        status = "VALID" if result["valid"] else "INVALID"
        print(f"{status} {fn}")
        if not result["valid"]:
            for err in result["errors"]:
                print(f"   -> {err}")

    # Search query tests
    query_tests = [
        {"debtor_name": "Acme Corporation", "state": "NY"},  # Valid
        {"debtor_name": "A"},  # Too short
        {"debtor_name": "'; DROP TABLE filings; --"},  # SQL injection
        {"debtor_name": "Test Corp", "state": "ZZ"},  # Invalid state
        {"debtor_name": "Test Corp", "filing_type": "UCC-5"},  # Invalid type
        {},  # Missing required field
    ]

    print("\n=== Search Query Validation ===")
    for query in query_tests:
        result = validate_search_query(query)
        status = "VALID" if result["valid"] else "INVALID"
        print(f"{status} {json.dumps(query)}")
        if not result["valid"]:
            for err in result["errors"]:
                print(f"   -> {err}")
