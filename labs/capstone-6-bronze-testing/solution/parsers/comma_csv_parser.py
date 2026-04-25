"""
Comma-Delimited CSV Parser for UCC Filing Source Files — SOLUTION
"""

import csv
import re
from io import StringIO
from pathlib import Path
from typing import Any


def parse_comma_csv(file_path: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Parse a comma-delimited CSV UCC filing source file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Source file not found: {file_path}")

    content = path.read_text(encoding="utf-8")
    lines = content.strip().split("\n")

    comment_lines = [l for l in lines if l.startswith("#")]
    data_lines = [l for l in lines if not l.startswith("#")]

    metadata = {
        "state": "",
        "record_count": 0,
        "format": "comma_csv",
    }
    for line in comment_lines:
        if "Record Count:" in line:
            match = re.search(r"Record Count:\s*(\d+)", line)
            if match:
                metadata["record_count"] = int(match.group(1))
        state_match = re.search(r"#\s+(\w+)\s+UCC", line)
        if state_match:
            metadata["state"] = state_match.group(1)

    records = []
    if data_lines:
        data_text = "\n".join(data_lines)
        reader = csv.DictReader(StringIO(data_text))
        for row in reader:
            record = {
                "filing_number": row.get("filing_number", "").strip(),
                "filing_type": row.get("filing_type", "").strip(),
                "filing_date": row.get("filing_date", "").strip(),
                "lapse_date": row.get("lapse_date", "").strip(),
                "status": row.get("status", "").strip(),
                "debtor_name": row.get("debtor_name", "").strip(),
                "debtor_address": row.get("debtor_address", "").strip(),
                "secured_party_name": row.get("secured_party_name", "").strip(),
                "collateral_description": row.get("collateral_description", "").strip(),
            }
            records.append(record)

    return records, metadata
