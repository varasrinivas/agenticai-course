"""
JSON Parser for UCC Filing Source Files — SOLUTION
"""

import json
from pathlib import Path
from typing import Any


def parse_json(file_path: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Parse a JSON UCC filing source file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Source file not found: {file_path}")

    # Explicitly use UTF-8 — will raise UnicodeDecodeError for UTF-16 files
    data = json.loads(path.read_text(encoding="utf-8"))

    raw_metadata = data.get("metadata", {})
    metadata = {
        "state": raw_metadata.get("state", ""),
        "record_count": raw_metadata.get("record_count", 0),
        "quarter": raw_metadata.get("quarter", ""),
        "format": "json",
    }

    records = []
    for filing in data.get("filings", []):
        record = {
            "filing_number": filing.get("filing_number", ""),
            "filing_type": filing.get("filing_type", ""),
            "filing_date": filing.get("filing_date", ""),
            "lapse_date": filing.get("lapse_date", ""),
            "status": filing.get("status", ""),
            "debtor_name": filing.get("debtor_name", ""),
            "debtor_address": filing.get("debtor_address", ""),
            "secured_party_name": filing.get("secured_party_name", ""),
            "collateral_description": filing.get("collateral_description", ""),
        }
        records.append(record)

    return records, metadata
