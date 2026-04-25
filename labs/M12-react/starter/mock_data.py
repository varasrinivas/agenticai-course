"""
M12 -- Mock Data (Complete -- do not modify)
============================================
Wraps the shared UCC mock data for this lab.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "shared"))

from mock_ucc_data import MOCK_FILINGS, ALL_FILINGS, search_filings, get_filing_by_number


if __name__ == "__main__":
    print(f"Mock data loaded: {len(ALL_FILINGS)} filings")
    for f in ALL_FILINGS[:3]:
        print(f"  {f['filing_number']} -- {f['debtor']['name']} ({f['state']})")
