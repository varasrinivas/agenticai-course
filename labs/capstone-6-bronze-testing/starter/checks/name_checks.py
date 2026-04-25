"""
NM-01: Name Normalization

Validates that debtor_name and secured_party_name are:
- All uppercase
- No leading/trailing whitespace
- No double spaces
"""

import re
from typing import Any


def check_name_normalization(
    state: str,
    bronze_records: list[dict],
    **kwargs,
) -> dict[str, Any]:
    """
    Check NM-01: Are names properly normalized?

    Args:
        state: State code
        bronze_records: Bronze table records

    Returns:
        Check result dict
    """
    # TODO 1: Check debtor_name and secured_party_name for each record
    # issues = []
    # for record in bronze_records:
    #     for field in ["debtor_name", "secured_party_name"]:
    #         value = record.get(field, "")
    #         problems = []
    #         if value != value.upper():
    #             problems.append("not_uppercase")
    #         if value != value.strip():
    #             problems.append("has_whitespace")
    #         if "  " in value:
    #             problems.append("double_spaces")
    #         if problems:
    #             issues.append({
    #                 "filing_number": record.get("filing_number"),
    #                 "field": field,
    #                 "value": value,
    #                 "problems": problems,
    #             })

    # TODO 2: Return PASS if no issues, FAIL if any found

    return {
        "check_id": "NM-01",
        "check_name": "Name Normalization",
        "status": "FAIL",
        "message": "Not implemented",
        "details": {},
    }
