"""
M15 Lab — Mock Data Wrapper
============================
Imports UCC filing data from the shared mock data module and exports
a DATA_FOR_SANDBOX string that can be injected into sandboxed code.

This file is COMPLETE — do not modify it.
"""

import json
import sys
import os

# Allow imports from the labs root (where shared/ lives)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from shared.mock_ucc_data import MOCK_FILINGS, EDGE_CASE_FILINGS, ALL_FILINGS


def _serialize_filings(filings: list[dict]) -> list[dict]:
    """Flatten nested debtor/secured_party dicts for sandbox consumption."""
    serializable = []
    for f in filings:
        serializable.append({
            "filing_number": f["filing_number"],
            "type": f["type"],
            "state": f["state"],
            "filing_date": f["filing_date"],
            "expiration_date": f["expiration_date"],
            "status": f["status"],
            "debtor_name": f["debtor"]["name"],
            "debtor_address": f["debtor"]["address"],
            "debtor_org_type": f["debtor"]["org_type"],
            "debtor_jurisdiction": f["debtor"]["jurisdiction"],
            "secured_party_name": f["secured_party"]["name"],
            "secured_party_address": f["secured_party"]["address"],
            "collateral_description": f["collateral_description"],
        })
    return serializable


# Serialized data as a Python literal string — eval-safe for the sandbox
# We use repr() instead of json.dumps() so that None stays as Python None
# (json.dumps would output "null" which is not valid Python)
_SERIALIZED = _serialize_filings(ALL_FILINGS)
DATA_FOR_SANDBOX = f"MOCK_FILINGS = {repr(_SERIALIZED)}\n"


if __name__ == "__main__":
    print(f"Mock data wrapper loaded: {len(ALL_FILINGS)} filings")
    print(f"DATA_FOR_SANDBOX length: {len(DATA_FOR_SANDBOX)} chars")
    print(f"First filing debtor: {ALL_FILINGS[0]['debtor']['name']}")
    print("Self-test passed.")
