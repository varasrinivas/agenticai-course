"""
M13 Lab — Mock Data Wrapper
============================
Re-exports shared mock UCC data so lab code can import locally.

Usage:
    from mock_data import search_filings, get_filing_by_number, ALL_FILINGS
"""

import sys
import os

# Add the shared directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from shared.mock_ucc_data import (
    MOCK_FILINGS,
    EDGE_CASE_FILINGS,
    ALL_FILINGS,
    get_filing_by_number,
    search_filings,
    get_states,
    get_stats,
)

__all__ = [
    "MOCK_FILINGS",
    "EDGE_CASE_FILINGS",
    "ALL_FILINGS",
    "get_filing_by_number",
    "search_filings",
    "get_states",
    "get_stats",
]

if __name__ == "__main__":
    stats = get_stats()
    print(f"Mock data loaded: {stats['total_filings']} filings across {len(stats['states'])} states")
