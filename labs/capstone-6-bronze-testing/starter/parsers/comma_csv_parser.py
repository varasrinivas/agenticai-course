"""
Comma-Delimited CSV Parser for UCC Filing Source Files

Parses standard comma-separated CSV files from states like DE, PA, MA.
Handles quoted fields (for addresses with commas), comment lines, and headers.

Returns:
    tuple: (records: list[dict], metadata: dict)
"""

import csv
from io import StringIO
from pathlib import Path
from typing import Any


def parse_comma_csv(file_path: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """
    Parse a comma-delimited CSV UCC filing source file.

    Args:
        file_path: Path to the comma CSV file

    Returns:
        Tuple of (records, metadata)

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file format is invalid
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Source file not found: {file_path}")

    # TODO 1: Read the file and separate comments from data
    content = ""  # TODO: path.read_text(encoding="utf-8")

    metadata = {
        "state": "",
        "record_count": 0,
        "format": "comma_csv",
    }

    # TODO 2: Filter out comment lines (# prefix) and parse metadata from them
    # Hint: Similar to pipe_csv_parser but delimiter is comma
    data_lines = []

    # TODO 3: Parse using csv.DictReader with default comma delimiter
    # IMPORTANT: Addresses contain commas and are quoted — csv module handles this
    records = []

    # TODO: Uncomment and complete:
    # data_text = "\n".join(data_lines)
    # reader = csv.DictReader(StringIO(data_text))
    # for row in reader:
    #     record = {
    #         "filing_number": row.get("filing_number", "").strip(),
    #         "filing_type": row.get("filing_type", "").strip(),
    #         "filing_date": row.get("filing_date", "").strip(),
    #         "lapse_date": row.get("lapse_date", "").strip(),
    #         "status": row.get("status", "").strip(),
    #         "debtor_name": row.get("debtor_name", "").strip(),
    #         "debtor_address": row.get("debtor_address", "").strip(),
    #         "secured_party_name": row.get("secured_party_name", "").strip(),
    #         "collateral_description": row.get("collateral_description", "").strip(),
    #     }
    #     records.append(record)

    return records, metadata
