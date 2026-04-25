"""CNT-01: Record Count Match — SOLUTION"""

from typing import Any


def check_record_count(
    state: str,
    source_records: list[dict] | None,
    bronze_records: list[dict],
    expected_count: int = 0,
    **kwargs,
) -> dict[str, Any]:
    """Check CNT-01: Do record counts match between source and Bronze?"""
    source_count = len(source_records) if source_records else 0
    bronze_count = len(bronze_records)

    details = {
        "source_count": source_count,
        "bronze_count": bronze_count,
        "expected_count": expected_count,
    }

    if source_count == bronze_count:
        return {
            "check_id": "CNT-01",
            "check_name": "Record Count Match",
            "status": "PASS",
            "message": f"Record counts match: {source_count} source = {bronze_count} bronze",
            "details": details,
        }
    else:
        return {
            "check_id": "CNT-01",
            "check_name": "Record Count Match",
            "status": "FAIL",
            "message": f"Count mismatch: {source_count} source vs {bronze_count} bronze (expected {expected_count})",
            "details": details,
        }
