"""DUP-01: No Duplicate Filing Numbers — SOLUTION"""

from collections import Counter
from typing import Any


def check_no_duplicates(
    state: str,
    bronze_records: list[dict],
    **kwargs,
) -> dict[str, Any]:
    """Check DUP-01: Are there any duplicate filing numbers?"""
    filing_numbers = [r.get("filing_number", "") for r in bronze_records]
    counts = Counter(filing_numbers)
    duplicates = {fn: count for fn, count in counts.items() if count > 1}

    details = {
        "total_records": len(bronze_records),
        "unique_filing_numbers": len(counts),
        "duplicates": duplicates,
    }

    if duplicates:
        return {
            "check_id": "DUP-01",
            "check_name": "No Duplicate Filing Numbers",
            "status": "WARN",
            "message": f"Found {len(duplicates)} duplicate filing numbers: {list(duplicates.keys())}",
            "details": details,
        }
    else:
        return {
            "check_id": "DUP-01",
            "check_name": "No Duplicate Filing Numbers",
            "status": "PASS",
            "message": f"No duplicates among {len(bronze_records)} records",
            "details": details,
        }
