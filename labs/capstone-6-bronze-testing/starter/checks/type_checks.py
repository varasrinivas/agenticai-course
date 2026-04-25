"""
FT-01: Filing Type Normalized

Validates that all filing_type values in Bronze are one of the
canonical normalized values.
"""

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
    """
    Check FT-01: Are all filing types normalized?

    Valid types: UCC1, UCC3_AMENDMENT, UCC3_CONTINUATION, UCC3_TERMINATION, UCC5

    Args:
        state: State code
        bronze_records: Bronze table records

    Returns:
        Check result dict
    """
    # TODO 1: Check each record's filing_type against VALID_FILING_TYPES
    # invalid = []
    # for record in bronze_records:
    #     ft = record.get("filing_type", "")
    #     if ft not in VALID_FILING_TYPES:
    #         invalid.append({
    #             "filing_number": record.get("filing_number"),
    #             "filing_type": ft,
    #         })

    # TODO 2: Return PASS if all valid, FAIL if any invalid

    return {
        "check_id": "FT-01",
        "check_name": "Filing Type Normalized",
        "status": "FAIL",
        "message": "Not implemented",
        "details": {},
    }
