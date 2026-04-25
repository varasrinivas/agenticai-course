"""
NL-01: Required Fields Not Null

Validates that mandatory fields are populated (not null, not empty string).
Required fields: filing_number, state, filing_type, filing_date, status, debtor_name
"""

from typing import Any

REQUIRED_FIELDS = [
    "filing_number",
    "state",
    "filing_type",
    "filing_date",
    "status",
    "debtor_name",
]


def check_required_fields_not_null(
    state: str,
    bronze_records: list[dict],
    **kwargs,
) -> dict[str, Any]:
    """
    Check NL-01: Are all required fields populated?

    Args:
        state: State code
        bronze_records: Bronze table records

    Returns:
        Check result dict
    """
    # TODO 1: Check each required field in each record
    # null_fields = []
    # for record in bronze_records:
    #     for field in REQUIRED_FIELDS:
    #         value = record.get(field)
    #         if value is None or (isinstance(value, str) and value.strip() == ""):
    #             null_fields.append({
    #                 "filing_number": record.get("filing_number", "UNKNOWN"),
    #                 "field": field,
    #             })

    # TODO 2: Return PASS if no nulls, FAIL with list of null fields

    return {
        "check_id": "NL-01",
        "check_name": "Required Fields Not Null",
        "status": "FAIL",
        "message": "Not implemented",
        "details": {},
    }
