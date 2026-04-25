"""FN-01: Filing Number Integrity — SOLUTION"""

import re
from typing import Any

FILING_NUMBER_PATTERN = re.compile(r"^[A-Z]{2}-\d{4}-\d{4}$")


def check_filing_number_integrity(
    state: str,
    bronze_records: list[dict],
    **kwargs,
) -> dict[str, Any]:
    """Check FN-01: Do all filing numbers match pattern XX-YYYY-NNNN?"""
    invalid = []
    wrong_state = []

    for record in bronze_records:
        fn = record.get("filing_number", "")
        if not FILING_NUMBER_PATTERN.match(fn):
            invalid.append(fn)
        elif not fn.startswith(f"{state}-"):
            wrong_state.append(fn)

    details = {
        "total_checked": len(bronze_records),
        "invalid_pattern": invalid,
        "wrong_state_prefix": wrong_state,
    }

    if invalid:
        return {
            "check_id": "FN-01",
            "check_name": "Filing Number Integrity",
            "status": "FAIL",
            "message": f"{len(invalid)} filing numbers have invalid format",
            "details": details,
        }
    elif wrong_state:
        return {
            "check_id": "FN-01",
            "check_name": "Filing Number Integrity",
            "status": "WARN",
            "message": f"{len(wrong_state)} filing numbers have wrong state prefix",
            "details": details,
        }
    else:
        return {
            "check_id": "FN-01",
            "check_name": "Filing Number Integrity",
            "status": "PASS",
            "message": f"All {len(bronze_records)} filing numbers valid",
            "details": details,
        }
