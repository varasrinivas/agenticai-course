"""
FN-01: Filing Number Integrity

Validates that all filing numbers in the Bronze table match the
expected pattern: XX-YYYY-NNNN (state-year-sequence).
"""

import re
from typing import Any

# Filing number pattern: 2-letter state, dash, 4-digit year, dash, 4-digit sequence
FILING_NUMBER_PATTERN = re.compile(r"^[A-Z]{2}-\d{4}-\d{4}$")


def check_filing_number_integrity(
    state: str,
    bronze_records: list[dict],
    **kwargs,
) -> dict[str, Any]:
    """
    Check FN-01: Do all filing numbers match pattern XX-YYYY-NNNN?

    Args:
        state: State code
        bronze_records: Bronze table records for this state

    Returns:
        Check result dict with any invalid filing numbers
    """
    # TODO 1: Iterate over bronze_records and check each filing_number
    # against FILING_NUMBER_PATTERN

    # TODO 2: Collect any records with invalid filing numbers
    # invalid = []
    # for record in bronze_records:
    #     fn = record.get("filing_number", "")
    #     if not FILING_NUMBER_PATTERN.match(fn):
    #         invalid.append(fn)

    # TODO 3: Also verify that the state prefix matches the expected state
    # e.g., NY records should have filing numbers starting with "NY-"
    # wrong_state = []
    # for record in bronze_records:
    #     fn = record.get("filing_number", "")
    #     if not fn.startswith(f"{state}-"):
    #         wrong_state.append(fn)

    # TODO 4: Return PASS if no issues, FAIL if any invalid patterns,
    # WARN if wrong state prefix

    return {
        "check_id": "FN-01",
        "check_name": "Filing Number Integrity",
        "status": "FAIL",
        "message": "Not implemented",
        "details": {},
    }
