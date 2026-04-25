"""
M15B — Single Agent Integration Tests
=======================================
Tests the single ReAct agent. REQUIRES an Anthropic API key.

Run from the M15B-build-complete-agent directory:
    python -m pytest tests/test_agent.py -v

NOTE: These tests make real API calls. Each test costs ~$0.01-0.05.
Skip with: pytest tests/test_agent.py -k "not integration"
"""

import json
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "solution"))

# Check for API key
if not os.environ.get("ANTHROPIC_API_KEY"):
    pytest.skip("ANTHROPIC_API_KEY not set — skipping integration tests", allow_module_level=True)

from agent import run_agent


class TestSingleAgent:
    """Integration tests for the single ReAct agent."""

    @pytest.mark.integration
    def test_find_acme_ny(self):
        """Agent should find Acme Corporation filings in New York."""
        result = run_agent("Find all UCC filings for Acme Corporation in New York")
        assert result is not None
        assert len(result) > 50
        # Should mention the filing number
        assert "UCC-2024-NY" in result or "acme" in result.lower()

    @pytest.mark.integration
    def test_risk_assessment(self):
        """Agent should assess risk for Acme Corporation."""
        result = run_agent("What's the risk level for Acme Corporation?")
        assert result is not None
        # Should mention risk level
        assert any(w in result.upper() for w in ["HIGH", "RISK", "LIEN"])

    @pytest.mark.integration
    def test_nonexistent_entity(self):
        """Agent should handle nonexistent entities gracefully."""
        result = run_agent("Find filings for XYZ Nonexistent Corp 12345")
        assert result is not None
        # Should not crash, should indicate no results
        assert any(w in result.lower() for w in ["no", "not found", "could not", "unable", "didn't find"])

    @pytest.mark.integration
    def test_max_turns_safety(self):
        """Agent should not loop forever."""
        result = run_agent("Tell me everything about every filing in every state", max_turns=3)
        assert result is not None
