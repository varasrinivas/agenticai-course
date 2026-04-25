"""NM-01: Name Normalization — SOLUTION"""

from typing import Any


def check_name_normalization(
    state: str,
    bronze_records: list[dict],
    **kwargs,
) -> dict[str, Any]:
    """Check NM-01: Are names properly normalized?"""
    issues = []
    for record in bronze_records:
        for field in ["debtor_name", "secured_party_name"]:
            value = record.get(field, "")
            if not value:
                continue
            problems = []
            if value != value.upper():
                problems.append("not_uppercase")
            if value != value.strip():
                problems.append("leading_trailing_whitespace")
            if "  " in value:
                problems.append("double_spaces")
            if problems:
                issues.append({
                    "filing_number": record.get("filing_number"),
                    "field": field,
                    "value": value,
                    "problems": problems,
                })

    if issues:
        return {
            "check_id": "NM-01",
            "check_name": "Name Normalization",
            "status": "FAIL",
            "message": f"{len(issues)} name fields have normalization issues",
            "details": {"issues": issues[:20]},
        }
    else:
        return {
            "check_id": "NM-01",
            "check_name": "Name Normalization",
            "status": "PASS",
            "message": f"All names properly normalized in {len(bronze_records)} records",
            "details": {},
        }
