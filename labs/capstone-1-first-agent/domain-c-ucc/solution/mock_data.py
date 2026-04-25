"""
Mock UCC Filing Records — Solution
(Re-exports from starter/mock_data.py so the solution runs standalone)
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "starter"))
from mock_data import UCC_FILINGS

__all__ = ["UCC_FILINGS"]
