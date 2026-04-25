"""
ST-01: Status Normalized

Validates that all status values are one of: ACTIVE, TERMINATED, LAPSED.
"""

from typing import Any

VALID_STATUSES = {"ACTIVE", "TERMINATED", "LAPSED"}


def check_status_normalized(
    state: str,
    bronze_records: list[dict],
    **kwargs,
) -> dict[str, Any]:
    """
    Check ST-01: Are all status values normalized?

    Args:
        state: State code
        bronze_records: Bronze table records

    Returns:
        Check result dict
    """
    # TODO 1: Check each record's status against VALID_STATUSES
    # invalid = []
    # for record in bronze_records:
    #     status = record.get("status", "")
    #     if status not in VALID_STATUSES:
    #         invalid.append({
    #             "filing_number": record.get("filing_number"),
    #             "status": status,
    #         })

    # TODO 2: Return PASS if all valid, FAIL if any invalid

    return {
        "check_id": "ST-01",
        "check_name": "Status Normalized",
        "status": "FAIL",
        "message": "Not implemented",
        "details": {},
    }
