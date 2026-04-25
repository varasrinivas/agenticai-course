"""
JSON Parser for UCC Filing Source Files

Parses JSON files from states like FL, NV.
Expected structure:
{
    "metadata": { "state": "FL", "record_count": 500, ... },
    "filings": [ { ... }, { ... } ]
}

Returns:
    tuple: (records: list[dict], metadata: dict)
"""

import json
from pathlib import Path
from typing import Any


def parse_json(file_path: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """
    Parse a JSON UCC filing source file.

    Args:
        file_path: Path to the JSON file

    Returns:
        Tuple of (records, metadata)

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If JSON is malformed or encoding is wrong
        UnicodeDecodeError: If encoding is not UTF-8
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Source file not found: {file_path}")

    # TODO 1: Read and parse the JSON file
    # IMPORTANT: Use UTF-8 encoding explicitly — some bad files use UTF-16
    # which will cause UnicodeDecodeError or json.JSONDecodeError
    data = {}  # TODO: json.loads(path.read_text(encoding="utf-8"))

    # TODO 2: Extract metadata
    # Hint: data["metadata"] contains state, record_count, quarter, etc.
    raw_metadata = {}  # TODO: data.get("metadata", {})
    metadata = {
        "state": "",        # TODO: raw_metadata.get("state", "")
        "record_count": 0,  # TODO: raw_metadata.get("record_count", 0)
        "format": "json",
    }

    # TODO 3: Extract filing records
    # Hint: data["filings"] is a list of filing objects
    # Each filing already has the expected field names
    records = []

    # TODO: Uncomment and complete:
    # for filing in data.get("filings", []):
    #     record = {
    #         "filing_number": filing.get("filing_number", ""),
    #         "filing_type": filing.get("filing_type", ""),
    #         "filing_date": filing.get("filing_date", ""),
    #         "lapse_date": filing.get("lapse_date", ""),
    #         "status": filing.get("status", ""),
    #         "debtor_name": filing.get("debtor_name", ""),
    #         "debtor_address": filing.get("debtor_address", ""),
    #         "secured_party_name": filing.get("secured_party_name", ""),
    #         "collateral_description": filing.get("collateral_description", ""),
    #     }
    #     records.append(record)

    return records, metadata
