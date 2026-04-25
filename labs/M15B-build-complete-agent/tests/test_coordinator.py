"""
M15B — Coordinator Multi-Agent Tests
======================================
Tests the coordinator + subagent system. REQUIRES an Anthropic API key.

Run from the M15B-build-complete-agent directory:
    python -m pytest tests/test_coordinator.py -v

NOTE: These tests make real API calls. Each test costs ~$0.02-0.10.
"""

import json
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "solution"))

if not os.environ.get("ANTHROPIC_API_KEY"):
    pytest.skip("ANTHROPIC_API_KEY not set — skipping integration tests", allow_module_level=True)

from coordinator import Coordinator, run_filing_search, run_risk_analysis


class TestSubagents:
    """Test individual subagents."""

    @pytest.mark.integration
    def test_filing_search_subagent(self):
        """Filing search subagent should return filing data."""
        result = run_filing_search("Find all UCC filings for Acme Corporation in New York")
        assert result is not None
        assert len(result) > 50
        assert any(w in result.lower() for w in ["acme", "ucc", "filing", "new york"])

    @pytest.mark.integration
    def test_risk_analysis_subagent(self):
        """Risk analysis subagent should return a risk assessment."""
        result = run_risk_analysis("Calculate the lien risk for Acme Corporation")
        assert result is not None
        assert any(w in result.upper() for w in ["HIGH", "MEDIUM", "LOW", "RISK"])


class TestCoordinator:
    """Test the full coordinator pipeline."""

    @pytest.mark.integration
    def test_single_turn_search(self):
        """Coordinator should handle a filing search query."""
        coord = Coordinator()
        result = coord.run("Find all UCC filings for Acme Corporation in New York")
        assert result is not None
        assert len(result) > 50

    @pytest.mark.integration
    def test_single_turn_risk(self):
        """Coordinator should handle a risk assessment query."""
        coord = Coordinator()
        result = coord.run("What's the risk level for Acme Corporation?")
        assert result is not None
        assert any(w in result.upper() for w in ["HIGH", "RISK"])

    @pytest.mark.integration
    def test_multi_turn_memory(self):
        """Coordinator should maintain conversation context across turns."""
        coord = Coordinator()

        # Turn 1
        r1 = coord.run("Find filings for Acme Corporation in New York")
        assert r1 is not None

        # Turn 2: follow-up should use context from Turn 1
        r2 = coord.run("What about their filings in Texas?")
        assert r2 is not None
        # Should reference Texas
        assert "texas" in r2.lower() or "TX" in r2

        # History should have entries
        assert len(coord.history) >= 4  # 2 user + 2 assistant

    @pytest.mark.integration
    def test_nonexistent_entity(self):
        """Coordinator should handle nonexistent entities gracefully."""
        coord = Coordinator()
        result = coord.run("Find filings for XYZ Nonexistent Corp 12345")
        assert result is not None
        # Should not crash
        assert any(w in result.lower() for w in ["no", "not found", "could not", "unable", "no filings"])
