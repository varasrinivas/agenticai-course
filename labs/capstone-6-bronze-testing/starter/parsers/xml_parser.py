"""
XML Parser for UCC Filing Source Files

Parses XML files from states like NY, IL, WA that use the standard
<ucc_filings> / <filing> XML schema.

Returns:
    tuple: (records: list[dict], metadata: dict)
        - records: list of dicts with normalized field names
        - metadata: dict with state, record_count, etc.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


def parse_xml(file_path: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """
    Parse an XML UCC filing source file.

    Args:
        file_path: Path to the XML file

    Returns:
        Tuple of (records, metadata)

    Raises:
        FileNotFoundError: If file doesn't exist
        xml.etree.ElementTree.ParseError: If XML is malformed
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Source file not found: {file_path}")

    # TODO 1: Parse the XML file using ElementTree
    # Hint: Use ET.parse() to load the file, then get the root element
    # The root element is <ucc_filings> with attributes: state, quarter, record_count
    tree = None  # Replace with ET.parse(file_path)
    root = None  # Replace with tree.getroot()

    # TODO 2: Extract metadata from root element attributes
    # Hint: root.attrib contains state, quarter, record_count, generated
    metadata = {
        "state": "",       # TODO: Extract from root.attrib["state"]
        "record_count": 0, # TODO: Extract from root.attrib["record_count"] (convert to int)
        "quarter": "",     # TODO: Extract from root.attrib["quarter"]
        "format": "xml",
    }

    # TODO 3: Iterate over <filing> elements and extract fields
    # Each <filing> has:
    #   - <filing_number>, <filing_type>, <filing_date>, <lapse_date>, <status>
    #   - <debtor> / <name>, <debtor> / <address>
    #   - <secured_party> / <name>
    #   - <collateral>
    records = []

    # TODO: Uncomment and complete:
    # for filing_elem in root.findall("filing"):
    #     record = {
    #         "filing_number": "",    # TODO: filing_elem.find("filing_number").text
    #         "filing_type": "",      # TODO: filing_elem.find("filing_type").text
    #         "filing_date": "",      # TODO: filing_elem.find("filing_date").text
    #         "lapse_date": "",       # TODO: filing_elem.find("lapse_date").text
    #         "status": "",           # TODO: filing_elem.find("status").text
    #         "debtor_name": "",      # TODO: filing_elem.find("debtor/name").text
    #         "debtor_address": "",   # TODO: filing_elem.find("debtor/address").text
    #         "secured_party_name": "",  # TODO: filing_elem.find("secured_party/name").text
    #         "collateral_description": "",  # TODO: filing_elem.find("collateral").text
    #     }
    #     records.append(record)

    return records, metadata
