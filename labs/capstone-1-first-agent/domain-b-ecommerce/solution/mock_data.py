"""
Mock B2B Ecommerce Order Records — Solution
(Re-exports from starter/mock_data.py so the solution runs standalone)
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "starter"))
from mock_data import ORDER_RECORDS

__all__ = ["ORDER_RECORDS"]
