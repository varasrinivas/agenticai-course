"""
Pipe-Delimited CSV Parser for UCC Filing Source Files

Parses pipe-delimited (|) CSV files from states like CA, OH, GA, CO.
Handles comment lines (starting with #) and header rows.

Returns:
    tuple: (records: list[dict], metadata: dict)
"""

import csv
from io import StringIO
from pathlib import Path
from typing import Any


def parse_pipe_csv(file_path: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """
    Parse a pipe-delimited CSV UCC filing source file.

    Args:
        file_path: Path to the pipe-delimited CSV file

    Returns:
        Tuple of (records, metadata)

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file format is invalid
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Source file not found: {file_path}")

    # TODO 1: Read the file content
    # Hint: Read with UTF-8 encoding
    content = ""  # TODO: path.read_text(encoding="utf-8")

    # TODO 2: Extract metadata from comment lines (lines starting with #)
    # Comment lines contain: state name, format, record count, date
    # Parse these to build the metadata dict
    metadata = {
        "state": "",
        "record_count": 0,
        "format": "pipe_csv",
    }

    # TODO 3: Filter out comment lines to get just the data
    # Hint: lines = [l for l in content.strip().split("\n") if not l.startswith("#")]
    # The first non-comment line is the header row
    data_lines = []  # TODO: Filter comment lines

    # TODO 4: Parse using csv.DictReader with delimiter="|"
    # Hint: Use StringIO to create a file-like object from the joined data_lines
    records = []

    # TODO: Uncomment and complete:
    # data_text = "\n".join(data_lines)
    # reader = csv.DictReader(StringIO(data_text), delimiter="|")
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

    # TODO 5: Extract record_count from comment metadata
    # Hint: Look for "Record Count:" in comment lines
    # for line in comment_lines:
    #     if "Record Count:" in line:
    #         metadata["record_count"] = int(line.split(":")[-1].strip())

    return records, metadata
