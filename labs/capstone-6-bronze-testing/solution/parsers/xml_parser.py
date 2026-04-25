"""
XML Parser for UCC Filing Source Files — SOLUTION
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


def parse_xml(file_path: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Parse an XML UCC filing source file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Source file not found: {file_path}")

    tree = ET.parse(file_path)
    root = tree.getroot()

    metadata = {
        "state": root.attrib.get("state", ""),
        "record_count": int(root.attrib.get("record_count", 0)),
        "quarter": root.attrib.get("quarter", ""),
        "format": "xml",
    }

    records = []
    for filing_elem in root.findall("filing"):
        record = {
            "filing_number": (filing_elem.find("filing_number").text or "").strip(),
            "filing_type": (filing_elem.find("filing_type").text or "").strip(),
            "filing_date": (filing_elem.find("filing_date").text or "").strip(),
            "lapse_date": (filing_elem.find("lapse_date").text or "").strip(),
            "status": (filing_elem.find("status").text or "").strip(),
            "debtor_name": (filing_elem.find("debtor/name").text or "").strip(),
            "debtor_address": (filing_elem.find("debtor/address").text or "").strip(),
            "secured_party_name": (filing_elem.find("secured_party/name").text or "").strip(),
            "collateral_description": (filing_elem.find("collateral").text or "").strip(),
        }
        records.append(record)

    return records, metadata
