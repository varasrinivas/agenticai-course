"""DT-01 and DT-02: Date Checks — SOLUTION"""

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
    """Check DT-01: Are all dates in YYYY-MM-DD format?"""
    invalid = []
    for record in bronze_records:
        for field in ["filing_date", "lapse_date"]:
            value = record.get(field, "")
            if value and not DATE_PATTERN.match(value):
                invalid.append({
                    "filing_number": record.get("filing_number"),
                    "field": field,
                    "value": value,
                })

    if invalid:
        return {
            "check_id": "DT-01",
            "check_name": "Date Format Valid",
            "status": "FAIL",
            "message": f"{len(invalid)} date fields have non-YYYY-MM-DD format",
            "details": {"invalid_dates": invalid[:20]},  # Cap at 20 for readability
        }
    else:
        return {
            "check_id": "DT-01",
            "check_name": "Date Format Valid",
            "status": "PASS",
            "message": f"All dates in {len(bronze_records)} records are YYYY-MM-DD",
            "details": {},
        }


def check_date_values(
    state: str,
    bronze_records: list[dict],
    **kwargs,
) -> dict[str, Any]:
    """Check DT-02: Are date values logically valid?"""
    lapse_before_filing = []
    future_dates = []
    unparseable = 0

    for record in bronze_records:
        try:
            fd_str = record.get("filing_date", "")
            ld_str = record.get("lapse_date", "")
            if not (DATE_PATTERN.match(fd_str) and DATE_PATTERN.match(ld_str)):
                unparseable += 1
                continue

            fd = datetime.strptime(fd_str, "%Y-%m-%d").date()
            ld = datetime.strptime(ld_str, "%Y-%m-%d").date()

            if ld < fd:
                lapse_before_filing.append({
                    "filing_number": record["filing_number"],
                    "filing_date": fd_str,
                    "lapse_date": ld_str,
                })
            if fd > MAX_FUTURE_DATE:
                future_dates.append({"filing_number": record["filing_number"], "field": "filing_date", "value": fd_str})
            if ld > MAX_FUTURE_DATE:
                future_dates.append({"filing_number": record["filing_number"], "field": "lapse_date", "value": ld_str})
        except (ValueError, KeyError):
            unparseable += 1

    details = {
        "lapse_before_filing": lapse_before_filing,
        "future_dates": future_dates,
        "unparseable_skipped": unparseable,
    }

    issues = len(lapse_before_filing) + len(future_dates)
    if issues > 0:
        return {
            "check_id": "DT-02",
            "check_name": "Date Values Valid",
            "status": "FAIL",
            "message": f"{len(lapse_before_filing)} records with lapse < filing, {len(future_dates)} future dates",
            "details": details,
        }
    else:
        return {
            "check_id": "DT-02",
            "check_name": "Date Values Valid",
            "status": "PASS",
            "message": f"All date values logically valid ({unparseable} skipped due to format)",
            "details": details,
        }
