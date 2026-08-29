"""
Fixed-Width Parser for UCC Filing Source Files

Parses fixed-width .dat files from states like TX.
Column positions are defined in a header line.

Expected column widths (from header):
    FILING_NUMBER: 15 chars
    FILING_TYPE: 20 chars
    FILING_DATE: 11 chars (10 + space)
    LAPSE_DATE: 11 chars
    STATUS: 11 chars (10 + space) -- starts at column 57
    DEBTOR_NAME: 51 chars (50 + space) -- starts at column 68, NOT 69
    DEBTOR_ADDRESS: 61 chars (60 + space) -- starts at column 119
    SECURED_PARTY: 51 chars (50 + space) -- starts at column 180
    COLLATERAL: remainder of line

Returns:
    tuple: (records: list[dict], metadata: dict)
"""

from pathlib import Path
from typing import Any


# Column specifications: (start_position, width)
# These correspond to the header: FILING_NUMBER(15) FILING_TYPE(20) etc.
COLUMN_SPECS = [
    ("filing_number", 0, 15),
    ("filing_type", 15, 20),
    ("filing_date", 35, 11),
    ("lapse_date", 46, 11),
    ("status", 57, 12),
    ("debtor_name", 69, 50),
    ("debtor_address", 119, 60),
    ("secured_party_name", 179, 50),
    ("collateral_description", 229, None),  # None = rest of line
]


def parse_fixed_width(file_path: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """
    Parse a fixed-width UCC filing source file.

    Args:
        file_path: Path to the .dat file

    Returns:
        Tuple of (records, metadata)

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file is truncated or malformed
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Source file not found: {file_path}")

    # TODO 1: Read the file content
    content = ""  # TODO: path.read_text(encoding="utf-8")

    # TODO 2: Split into lines and separate header lines from data
    # First 3 lines are headers:
    #   Line 1: Title with record count
    #   Line 2: Generated date
    #   Line 3: Column definitions
    # Data starts at line 4 (index 3)
    lines = []  # TODO: content.strip().split("\n")

    metadata = {
        "state": "",
        "record_count": 0,
        "format": "fixed_width",
    }

    # TODO 3: Parse metadata from header lines
    # Hint: Line 1 contains "RECORD COUNT: 600"
    # Extract with: int(lines[0].split("RECORD COUNT:")[-1].strip())

    # TODO 4: Parse each data line using COLUMN_SPECS
    # For each column, extract substring using start position and width
    records = []

    # TODO: Uncomment and complete:
    # for line_num, line in enumerate(lines[3:], start=4):
    #     if not line.strip():
    #         continue
    #     record = {}
    #     try:
    #         for field_name, start, width in COLUMN_SPECS:
    #             if width is None:
    #                 value = line[start:].strip()
    #             else:
    #                 value = line[start:start + width].strip()
    #             record[field_name] = value
    #     except IndexError:
    #         raise ValueError(
    #             f"Line {line_num} is truncated (expected >= 229 chars, got {len(line)}). "
    #             f"File may be corrupted."
    #         )
    #     records.append(record)

    return records, metadata
