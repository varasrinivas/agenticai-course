"""NL-01: Required Fields Not Null — SOLUTION"""

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
    """Check NL-01: Are all required fields populated?"""
    null_fields = []
    for record in bronze_records:
        for field in REQUIRED_FIELDS:
            value = record.get(field)
            if value is None or (isinstance(value, str) and value.strip() == ""):
                null_fields.append({
                    "filing_number": record.get("filing_number", "UNKNOWN"),
                    "field": field,
                })

    if null_fields:
        return {
            "check_id": "NL-01",
            "check_name": "Required Fields Not Null",
            "status": "FAIL",
            "message": f"{len(null_fields)} required fields are null/empty",
            "details": {"null_fields": null_fields[:20]},
        }
    else:
        return {
            "check_id": "NL-01",
            "check_name": "Required Fields Not Null",
            "status": "PASS",
            "message": f"All required fields populated in {len(bronze_records)} records",
            "details": {},
        }
