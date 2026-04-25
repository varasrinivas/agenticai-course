"""
CNT-01: Record Count Match

Validates that the number of records in the source file matches
the number of records loaded into the Bronze table for this state.
"""

from typing import Any


def check_record_count(
    state: str,
    source_records: list[dict] | None,
    bronze_records: list[dict],
    expected_count: int = 0,
    **kwargs,
) -> dict[str, Any]:
    """
    Check CNT-01: Do record counts match between source and Bronze?

    Args:
        state: State code
        source_records: Parsed source records
        bronze_records: Bronze table records for this state
        expected_count: Expected count from load manifest

    Returns:
        Check result dict
    """
    # TODO 1: Get source count and bronze count
    # source_count = len(source_records) if source_records else 0
    # bronze_count = len(bronze_records)

    # TODO 2: Compare counts
    # If source_count == bronze_count: PASS
    # If counts differ: FAIL with details showing both counts

    # TODO 3: Also compare against expected_count from manifest if provided
    # This catches cases where BOTH source and bronze are wrong

    return {
        "check_id": "CNT-01",
        "check_name": "Record Count Match",
        "status": "FAIL",
        "message": "Not implemented",
        "details": {},
    }
