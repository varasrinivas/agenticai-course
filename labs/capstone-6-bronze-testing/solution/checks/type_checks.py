"""FT-01: Filing Type Normalized — SOLUTION"""

from typing import Any

VALID_FILING_TYPES = {
    "UCC1",
    "UCC3_AMENDMENT",
    "UCC3_CONTINUATION",
    "UCC3_TERMINATION",
    "UCC5",
}


def check_filing_type_normalized(
    state: str,
    bronze_records: list[dict],
    **kwargs,
) -> dict[str, Any]:
    """Check FT-01: Are all filing types normalized?"""
    invalid = []
    for record in bronze_records:
        ft = record.get("filing_type", "")
        if ft not in VALID_FILING_TYPES:
            invalid.append({
                "filing_number": record.get("filing_number"),
                "filing_type": ft,
            })

    if invalid:
        return {
            "check_id": "FT-01",
            "check_name": "Filing Type Normalized",
            "status": "FAIL",
            "message": f"{len(invalid)} records have non-standard filing types",
            "details": {"invalid_records": invalid},
        }
    else:
        return {
            "check_id": "FT-01",
            "check_name": "Filing Type Normalized",
            "status": "PASS",
            "message": f"All {len(bronze_records)} records have valid filing types",
            "details": {"valid_types_found": list({r.get("filing_type") for r in bronze_records})},
        }
