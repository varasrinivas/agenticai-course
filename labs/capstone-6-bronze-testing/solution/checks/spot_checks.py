"""SP-01: Spot Check Sample Records — SOLUTION"""

import random
from typing import Any


def check_spot_sample(
    state: str,
    source_records: list[dict] | None,
    bronze_records: list[dict],
    **kwargs,
) -> dict[str, Any]:
    """Check SP-01: Do random Bronze records match their source?"""
    if not source_records:
        return {
            "check_id": "SP-01",
            "check_name": "Spot Check Sample",
            "status": "FAIL",
            "message": "Cannot spot check — source records not available",
            "details": {},
        }

    source_lookup = {r["filing_number"]: r for r in source_records}

    sample_size = min(3, len(bronze_records))
    if sample_size == 0:
        return {
            "check_id": "SP-01",
            "check_name": "Spot Check Sample",
            "status": "FAIL",
            "message": "No bronze records to spot check",
            "details": {},
        }

    samples = random.sample(bronze_records, sample_size)

    mismatches = []
    checked = []
    for bronze_rec in samples:
        fn = bronze_rec.get("filing_number", "")
        source_rec = source_lookup.get(fn)
        if not source_rec:
            mismatches.append({"filing_number": fn, "issue": "not_found_in_source"})
            checked.append(fn)
            continue

        # Compare debtor_name (case-insensitive since Bronze is normalized uppercase)
        b_name = bronze_rec.get("debtor_name", "").upper().strip()
        s_name = source_rec.get("debtor_name", "").upper().strip()
        if b_name != s_name:
            mismatches.append({
                "filing_number": fn,
                "field": "debtor_name",
                "bronze": bronze_rec.get("debtor_name"),
                "source": source_rec.get("debtor_name"),
            })

        # Compare secured_party_name
        b_sp = bronze_rec.get("secured_party_name", "").upper().strip()
        s_sp = source_rec.get("secured_party_name", "").upper().strip()
        if b_sp != s_sp:
            mismatches.append({
                "filing_number": fn,
                "field": "secured_party_name",
                "bronze": bronze_rec.get("secured_party_name"),
                "source": source_rec.get("secured_party_name"),
            })

        checked.append(fn)

    details = {"checked_records": checked, "mismatches": mismatches}

    if mismatches:
        return {
            "check_id": "SP-01",
            "check_name": "Spot Check Sample",
            "status": "FAIL",
            "message": f"{len(mismatches)} mismatches in {sample_size} spot-checked records",
            "details": details,
        }
    else:
        return {
            "check_id": "SP-01",
            "check_name": "Spot Check Sample",
            "status": "PASS",
            "message": f"All {sample_size} spot-checked records match source",
            "details": details,
        }
