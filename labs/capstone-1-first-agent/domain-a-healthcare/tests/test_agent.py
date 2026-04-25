"""
Tests for Healthcare Pre-Auth Status Checker Agent — Domain A
================================================================
5 test scenarios: 3 happy path, 1 edge case, 1 error case.

Run from the domain-a-healthcare directory:
    python -m pytest tests/
"""

import sys
import os

# Add the solution directory to the path so we can import the tools module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "solution"))

from tools import get_preauth_status


# ──────────────────────────────────────────────────────────────
# Happy Path Tests
# ──────────────────────────────────────────────────────────────

class TestGetPreauthStatusHappyPath:
    """Tests for valid pre-authorization lookups."""

    def test_approved_status(self):
        """PA-2024-00142 should return an approved total knee replacement."""
        result = get_preauth_status("PA-2024-00142")

        assert "error" not in result
        assert result["status"] == "approved"
        assert result["reference_id"] == "PA-2024-00142"
        assert result["patient_name"] == "Maria Gonzalez"
        assert result["cpt_code"] == "27447"

    def test_denied_status(self):
        """PA-2024-00398 should return a denied lumbar laminotomy."""
        result = get_preauth_status("PA-2024-00398")

        assert "error" not in result
        assert result["status"] == "denied"
        assert result["reference_id"] == "PA-2024-00398"
        assert result["patient_name"] == "James O'Brien"
        assert result["cpt_code"] == "63030"

    def test_pending_status(self):
        """PA-2024-00278 should return a pending CABG request."""
        result = get_preauth_status("PA-2024-00278")

        assert "error" not in result
        assert result["status"] == "pending"
        assert result["reference_id"] == "PA-2024-00278"
        assert result["patient_name"] == "Robert Williams"
        assert result["determination_date"] is None


# ──────────────────────────────────────────────────────────────
# Edge Case Tests
# ──────────────────────────────────────────────────────────────

class TestGetPreauthStatusEdgeCases:
    """Tests for edge-case inputs."""

    def test_nonexistent_reference_id(self):
        """A reference ID that does not exist should return an error dict."""
        result = get_preauth_status("PA-9999-00000")

        assert "error" in result
        assert "PA-9999-00000" in result["error"]
        assert "suggestion" in result


# ──────────────────────────────────────────────────────────────
# Error Case Tests
# ──────────────────────────────────────────────────────────────

class TestGetPreauthStatusErrors:
    """Tests for invalid inputs."""

    def test_empty_string_reference_id(self):
        """An empty string should return an error dict (no match)."""
        result = get_preauth_status("")

        assert "error" in result
        assert "suggestion" in result
