"""
Fixed-Width Parser for UCC Filing Source Files — SOLUTION
"""

import re
from pathlib import Path
from typing import Any

COLUMN_SPECS = [
    ("filing_number", 0, 15),
    ("filing_type", 15, 20),
    ("filing_date", 35, 11),
    ("lapse_date", 46, 11),
    ("status", 57, 12),
    ("debtor_name", 69, 50),
    ("debtor_address", 119, 60),
    ("secured_party_name", 179, 50),
    ("collateral_description", 229, None),
]


def parse_fixed_width(file_path: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Parse a fixed-width UCC filing source file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Source file not found: {file_path}")

    content = path.read_text(encoding="utf-8")
    lines = content.strip().split("\n")

    if len(lines) < 4:
        raise ValueError(f"File has only {len(lines)} lines — expected at least 4 (3 header + 1 data)")

    # Extract metadata from header
    metadata = {
        "state": "",
        "record_count": 0,
        "format": "fixed_width",
    }

    count_match = re.search(r"RECORD COUNT:\s*(\d+)", lines[0])
    if count_match:
        metadata["record_count"] = int(count_match.group(1))

    state_match = re.search(r"^(\w+)\s+UCC", lines[0])
    if state_match:
        metadata["state"] = state_match.group(1)

    # Parse data lines (starting at index 3)
    records = []
    for line_num, line in enumerate(lines[3:], start=4):
        if not line.strip():
            continue

        record = {}
        try:
            for field_name, start, width in COLUMN_SPECS:
                if width is None:
                    value = line[start:].strip()
                else:
                    if start + width > len(line) + 5:  # Allow small tolerance
                        raise IndexError(f"Column {field_name} extends beyond line length")
                    value = line[start:start + width].strip()
                record[field_name] = value
        except IndexError as e:
            raise ValueError(
                f"Line {line_num} is truncated (expected >= 229 chars, got {len(line)}). "
                f"File may be corrupted. Detail: {e}"
            )

        records.append(record)

    return records, metadata
