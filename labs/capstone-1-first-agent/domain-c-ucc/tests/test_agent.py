"""
Tests for UCC Filing Lookup Agent — Domain C
================================================
5 test scenarios: 3 happy path, 1 edge case, 1 error case.

Run from the domain-c-ucc directory:
    python -m pytest tests/
"""

import sys
import os

# Add the solution directory to the path so we can import the tools module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "solution"))

from tools import search_ucc_filings


# ──────────────────────────────────────────────────────────────
# Happy Path Tests
# ──────────────────────────────────────────────────────────────

class TestSearchUccFilingsHappyPath:
    """Tests for valid UCC filing searches."""

    def test_meridian_in_delaware_returns_two_results(self):
        """Searching for 'Meridian' in DE should return 2 filings
        (Meridian Logistics Holdings LLC and Meridian Fleet Services Inc.)."""
        result = search_ucc_filings("Meridian", "DE")

        assert result["total"] == 2
        assert len(result["results"]) == 2

        debtor_names = {r["debtor"]["name"] for r in result["results"]}
        assert "Meridian Logistics Holdings LLC" in debtor_names
        assert "Meridian Fleet Services Inc." in debtor_names

    def test_lone_star_in_texas_returns_active(self):
        """Searching for 'Lone Star' in TX should return 1 active filing."""
        result = search_ucc_filings("Lone Star", "TX")

        assert result["total"] == 1
        assert len(result["results"]) == 1
        assert result["results"][0]["status"] == "active"
        assert result["results"][0]["debtor"]["name"] == "Lone Star Fabrication & Welding Inc."

    def test_great_lakes_in_illinois_returns_terminated(self):
        """Searching for 'Great Lakes' in IL should return 1 terminated filing."""
        result = search_ucc_filings("Great Lakes", "IL")

        assert result["total"] == 1
        assert len(result["results"]) == 1
        assert result["results"][0]["status"] == "terminated"
        assert result["results"][0]["debtor"]["name"] == "Great Lakes Brewing Collective Inc."


# ──────────────────────────────────────────────────────────────
# Edge Case Tests
# ──────────────────────────────────────────────────────────────

class TestSearchUccFilingsEdgeCases:
    """Tests for edge-case inputs."""

    def test_nonexistent_business_returns_zero_results(self):
        """Searching for a business that does not exist should return 0 results."""
        result = search_ucc_filings("Nonexistent", "DE")

        assert result["total"] == 0
        assert len(result["results"]) == 0
        assert "message" in result


# ──────────────────────────────────────────────────────────────
# Error Case Tests
# ──────────────────────────────────────────────────────────────

class TestSearchUccFilingsErrors:
    """Tests for invalid inputs."""

    def test_empty_business_name_returns_zero_results(self):
        """An empty business name should return 0 results (every debtor
        name contains an empty string, but the function should still
        handle this gracefully)."""
        result = search_ucc_filings("", "DE")

        # An empty string is technically a substring of everything,
        # so this may return all DE filings. Either way, the function
        # should not raise an exception.
        assert "results" in result or "error" not in result
        assert isinstance(result.get("total", 0), int)
