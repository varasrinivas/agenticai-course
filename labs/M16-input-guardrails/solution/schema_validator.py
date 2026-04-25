"""
M16: Schema Validator — Solution
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

    # Check basic format with regex
    if not re.match(FILING_NUMBER_PATTERN, filing_number):
        errors.append(f"Filing number '{filing_number}' does not match expected format UCC-YYYY-SS-NNNNNNN")
        return {"valid": False, "errors": errors, "parsed": None}

    # Extract and validate components
    parts = filing_number.split("-")
    # parts = ["UCC", "YYYY", "SS", "NNNNNNN"]
    year = int(parts[1])
    state = parts[2]
    sequence = parts[3]

    if year < 2000 or year > 2030:
        errors.append(f"Year {year} is out of valid range (2000-2030)")

    if state not in VALID_STATES:
        errors.append(f"Invalid state code '{state}'")

    if len(errors) == 0:
        parsed = {
            "year": year,
            "state": state,
            "sequence": sequence,
        }

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

    # Validate debtor_name (required)
    debtor_name = query.get("debtor_name")
    if not debtor_name or not isinstance(debtor_name, str) or debtor_name.strip() == "":
        errors.append("debtor_name is required and must be a non-empty string")
    else:
        debtor_name = debtor_name.strip()
        if len(debtor_name) < 2 or len(debtor_name) > 100:
            errors.append("debtor_name must be 2-100 characters")
        # Check for SQL injection characters
        injection_patterns = [";", "--", "'", '"', "DROP", "DELETE", "SELECT"]
        for pattern in injection_patterns:
            if pattern.lower() in debtor_name.lower():
                errors.append(f"debtor_name contains prohibited characters")
                break
        sanitized["debtor_name"] = debtor_name

    # Validate state (optional)
    state = query.get("state")
    if state is not None:
        if not isinstance(state, str) or not re.match(r"^[A-Z]{2}$", state):
            errors.append(f"State must be a 2-letter uppercase code, got '{state}'")
        elif state not in VALID_STATES:
            errors.append(f"Invalid state code '{state}'")
        else:
            sanitized["state"] = state

    # Validate filing_type (optional)
    filing_type = query.get("filing_type")
    if filing_type is not None:
        valid_types = {"UCC-1", "UCC-3"}
        if filing_type not in valid_types:
            errors.append(f"filing_type must be one of {valid_types}, got '{filing_type}'")
        else:
            sanitized["filing_type"] = filing_type

    # Validate status (optional)
    status = query.get("status")
    if status is not None:
        valid_statuses = {"Active", "Terminated", "Lapsed", "Amendment"}
        if status not in valid_statuses:
            errors.append(f"status must be one of {valid_statuses}, got '{status}'")
        else:
            sanitized["status"] = status

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
