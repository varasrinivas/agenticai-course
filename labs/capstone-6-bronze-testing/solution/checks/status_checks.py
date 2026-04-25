"""ST-01: Status Normalized — SOLUTION"""

from typing import Any

VALID_STATUSES = {"ACTIVE", "TERMINATED", "LAPSED"}


def check_status_normalized(
    state: str,
    bronze_records: list[dict],
    **kwargs,
) -> dict[str, Any]:
    """Check ST-01: Are all status values normalized?"""
    invalid = []
    for record in bronze_records:
        status = record.get("status", "")
        if status not in VALID_STATUSES:
            invalid.append({
                "filing_number": record.get("filing_number"),
                "status": status,
            })

    if invalid:
        return {
            "check_id": "ST-01",
            "check_name": "Status Normalized",
            "status": "FAIL",
            "message": f"{len(invalid)} records have non-standard status values",
            "details": {"invalid_records": invalid},
        }
    else:
        return {
            "check_id": "ST-01",
            "check_name": "Status Normalized",
            "status": "PASS",
            "message": f"All {len(bronze_records)} records have valid status values",
            "details": {"statuses_found": list({r.get("status") for r in bronze_records})},
        }
