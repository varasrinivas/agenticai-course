"""
Mock Pre-Authorization Records — Solution
(Identical to starter/mock_data.py — included here so the solution runs standalone)
"""

# Re-export from starter
import sys
import os

# Add starter directory to path so we can reuse the same mock data
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "starter"))
from mock_data import PREAUTH_RECORDS

__all__ = ["PREAUTH_RECORDS"]
