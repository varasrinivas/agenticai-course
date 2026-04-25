"""
SP-01: Spot Check Sample Records

Picks 3 random records from the Bronze table and verifies their
field values match the corresponding source file records.
"""

import random
from typing import Any


def check_spot_sample(
    state: str,
    source_records: list[dict] | None,
    bronze_records: list[dict],
    **kwargs,
) -> dict[str, Any]:
    """
    Check SP-01: Do random Bronze records match their source?

    Picks 3 random records from bronze_records, finds the matching
    record in source_records by filing_number, and compares key fields.

    Args:
        state: State code
        source_records: Parsed source records
        bronze_records: Bronze table records

    Returns:
        Check result dict
    """
    if not source_records:
        return {
            "check_id": "SP-01",
            "check_name": "Spot Check Sample",
            "status": "FAIL",
            "message": "Cannot spot check — source records not available",
            "details": {},
        }

    # TODO 1: Build a lookup dict from source records keyed by filing_number
    # source_lookup = {r["filing_number"]: r for r in source_records}

    # TODO 2: Pick 3 random bronze records (or fewer if less than 3 exist)
    # sample_size = min(3, len(bronze_records))
    # samples = random.sample(bronze_records, sample_size)

    # TODO 3: For each sampled record, find the matching source record
    # and compare fields: debtor_name, debtor_address, secured_party_name
    # Note: source fields may not be normalized yet — compare carefully
    # mismatches = []
    # checked = []
    # for bronze_rec in samples:
    #     fn = bronze_rec["filing_number"]
    #     source_rec = source_lookup.get(fn)
    #     if not source_rec:
    #         mismatches.append({"filing_number": fn, "issue": "not_found_in_source"})
    #         continue
    #     # Compare debtor_name (Bronze should be uppercase normalized)
    #     if bronze_rec.get("debtor_name", "").upper() != source_rec.get("debtor_name", "").upper():
    #         mismatches.append({
    #             "filing_number": fn,
    #             "field": "debtor_name",
    #             "bronze": bronze_rec.get("debtor_name"),
    #             "source": source_rec.get("debtor_name"),
    #         })
    #     checked.append(fn)

    # TODO 4: Return PASS if all match, FAIL if any mismatch

    return {
        "check_id": "SP-01",
        "check_name": "Spot Check Sample",
        "status": "FAIL",
        "message": "Not implemented",
        "details": {},
    }
