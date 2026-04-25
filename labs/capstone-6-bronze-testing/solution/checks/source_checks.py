"""SRC-01: Source File Parseable — SOLUTION"""

from typing import Any


def check_source_parseable(
    state: str,
    source_file: str,
    source_records: list[dict] | None,
    bronze_records: list[dict],
    parse_error: str | None = None,
    **kwargs,
) -> dict[str, Any]:
    """Check SRC-01: Can the source file be parsed?"""
    if parse_error is not None:
        return {
            "check_id": "SRC-01",
            "check_name": "Source File Parseable",
            "status": "FAIL",
            "message": f"Failed to parse source file: {parse_error}",
            "details": {"error": parse_error, "source_file": source_file},
        }

    if source_records is None or len(source_records) == 0:
        return {
            "check_id": "SRC-01",
            "check_name": "Source File Parseable",
            "status": "FAIL",
            "message": "Source file parsed but returned 0 records",
            "details": {"source_file": source_file},
        }

    return {
        "check_id": "SRC-01",
        "check_name": "Source File Parseable",
        "status": "PASS",
        "message": f"Successfully parsed {len(source_records)} records from source",
        "details": {"record_count": len(source_records), "source_file": source_file},
    }
