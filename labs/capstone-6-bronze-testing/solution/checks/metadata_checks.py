"""LM-01: Load Metadata Present — SOLUTION"""

from typing import Any

METADATA_FIELDS = ["load_timestamp", "load_batch_id", "source_file"]


def check_load_metadata(
    state: str,
    bronze_records: list[dict],
    **kwargs,
) -> dict[str, Any]:
    """Check LM-01: Are load metadata fields populated?"""
    missing = []
    for record in bronze_records:
        for field in METADATA_FIELDS:
            value = record.get(field)
            if value is None or (isinstance(value, str) and value.strip() == ""):
                missing.append({
                    "filing_number": record.get("filing_number", "UNKNOWN"),
                    "field": field,
                })

    if missing:
        return {
            "check_id": "LM-01",
            "check_name": "Load Metadata Present",
            "status": "FAIL",
            "message": f"{len(missing)} metadata fields missing",
            "details": {"missing": missing[:20]},
        }
    else:
        return {
            "check_id": "LM-01",
            "check_name": "Load Metadata Present",
            "status": "PASS",
            "message": f"All load metadata present in {len(bronze_records)} records",
            "details": {},
        }
