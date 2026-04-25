"""
DT-01: Date Format Valid
DT-02: Date Values Valid

DT-01 checks that all date fields are in YYYY-MM-DD format.
DT-02 checks that date values are logically valid:
  - lapse_date >= filing_date
  - No future dates beyond 2030
"""

import re
from datetime import date, datetime
from typing import Any

DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MAX_FUTURE_DATE = date(2030, 12, 31)


def check_date_format(
    state: str,
    bronze_records: list[dict],
    **kwargs,
) -> dict[str, Any]:
    """
    Check DT-01: Are all dates in YYYY-MM-DD format?

    Checks both filing_date and lapse_date fields.

    Args:
        state: State code
        bronze_records: Bronze table records

    Returns:
        Check result dict
    """
    # TODO 1: Check filing_date and lapse_date for each record
    # invalid = []
    # for record in bronze_records:
    #     for field in ["filing_date", "lapse_date"]:
    #         value = record.get(field, "")
    #         if value and not DATE_PATTERN.match(value):
    #             invalid.append({
    #                 "filing_number": record.get("filing_number"),
    #                 "field": field,
    #                 "value": value,
    #             })

    # TODO 2: Return FAIL if any invalid dates (like GA's DD/MM/YYYY dates)

    return {
        "check_id": "DT-01",
        "check_name": "Date Format Valid",
        "status": "FAIL",
        "message": "Not implemented",
        "details": {},
    }


def check_date_values(
    state: str,
    bronze_records: list[dict],
    **kwargs,
) -> dict[str, Any]:
    """
    Check DT-02: Are date values logically valid?

    Rules:
    - lapse_date >= filing_date (lapse can't be before filing)
    - No dates beyond 2030-12-31

    Args:
        state: State code
        bronze_records: Bronze table records

    Returns:
        Check result dict
    """
    # TODO 1: Parse dates and check lapse_date >= filing_date
    # lapse_before_filing = []
    # future_dates = []
    # for record in bronze_records:
    #     try:
    #         fd = datetime.strptime(record["filing_date"], "%Y-%m-%d").date()
    #         ld = datetime.strptime(record["lapse_date"], "%Y-%m-%d").date()
    #         if ld < fd:
    #             lapse_before_filing.append({
    #                 "filing_number": record["filing_number"],
    #                 "filing_date": record["filing_date"],
    #                 "lapse_date": record["lapse_date"],
    #             })
    #         if fd > MAX_FUTURE_DATE or ld > MAX_FUTURE_DATE:
    #             future_dates.append(record["filing_number"])
    #     except (ValueError, KeyError):
    #         pass  # Skip records with unparseable dates (caught by DT-01)

    # TODO 2: Return FAIL if lapse < filing found (like NY-2024-0004 and NY-2024-0009)

    return {
        "check_id": "DT-02",
        "check_name": "Date Values Valid",
        "status": "FAIL",
        "message": "Not implemented",
        "details": {},
    }
