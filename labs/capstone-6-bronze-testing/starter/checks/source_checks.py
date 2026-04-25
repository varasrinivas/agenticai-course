"""
SRC-01: Source File Parseable

Validates that the source file can be read and parsed without errors.
This is the first check — if it fails, subsequent checks are skipped.
"""

from typing import Any


def check_source_parseable(
    state: str,
    source_file: str,
    source_records: list[dict] | None,
    bronze_records: list[dict],
    parse_error: str | None = None,
    **kwargs,
) -> dict[str, Any]:
    """
    Check SRC-01: Can the source file be parsed?

    Args:
        state: State code (e.g., "NY")
        source_file: Path to source file
        source_records: Parsed records (None if parsing failed)
        bronze_records: Records from Bronze table for this state
        parse_error: Error message if parsing failed

    Returns:
        Check result dict
    """
    # TODO 1: If parse_error is not None, the file failed to parse
    # Return FAIL status with the error message

    # TODO 2: If source_records is None or empty, return FAIL

    # TODO 3: If parsing succeeded, return PASS with record count

    # TODO: Replace this stub:
    return {
        "check_id": "SRC-01",
        "check_name": "Source File Parseable",
        "status": "FAIL",
        "message": "Not implemented",
        "details": {},
    }
