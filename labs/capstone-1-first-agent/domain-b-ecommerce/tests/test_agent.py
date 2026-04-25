"""
Tests for B2B Ecommerce Order Status Bot — Domain B
======================================================
5 test scenarios: 3 happy path, 1 edge case, 1 error case.

Run from the domain-b-ecommerce directory:
    python -m pytest tests/
"""

import sys
import os

# Add the solution directory to the path so we can import the tools module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "solution"))

from tools import get_order_status


# ──────────────────────────────────────────────────────────────
# Happy Path Tests
# ──────────────────────────────────────────────────────────────

class TestGetOrderStatusHappyPath:
    """Tests for valid order lookups."""

    def test_shipped_status(self):
        """PO-2024-8847 should return a shipped order for Apex Manufacturing."""
        result = get_order_status("PO-2024-8847")

        assert "error" not in result
        assert result["status"] == "shipped"
        assert result["po_number"] == "PO-2024-8847"
        assert result["customer_name"] == "Apex Manufacturing Co."
        assert result["carrier"] == "FedEx Freight"

    def test_delivered_status(self):
        """PO-2024-8512 should return a delivered order for Pacific Coast Electronics."""
        result = get_order_status("PO-2024-8512")

        assert "error" not in result
        assert result["status"] == "delivered"
        assert result["po_number"] == "PO-2024-8512"
        assert result["customer_name"] == "Pacific Coast Electronics"
        assert result["payment_status"] == "paid"

    def test_backordered_status(self):
        """PO-2024-9250 should return a backordered order for Summit HVAC."""
        result = get_order_status("PO-2024-9250")

        assert "error" not in result
        assert result["status"] == "backordered"
        assert result["po_number"] == "PO-2024-9250"
        assert result["customer_name"] == "Summit HVAC Solutions"
        assert result["ship_date"] is None


# ──────────────────────────────────────────────────────────────
# Edge Case Tests
# ──────────────────────────────────────────────────────────────

class TestGetOrderStatusEdgeCases:
    """Tests for edge-case inputs."""

    def test_nonexistent_po_number(self):
        """A PO number that does not exist should return an error dict."""
        result = get_order_status("PO-9999-0000")

        assert "error" in result
        assert "PO-9999-0000" in result["error"]
        assert "suggestion" in result


# ──────────────────────────────────────────────────────────────
# Error Case Tests
# ──────────────────────────────────────────────────────────────

class TestGetOrderStatusErrors:
    """Tests for invalid inputs."""

    def test_empty_string_po_number(self):
        """An empty string should return an error dict (no match)."""
        result = get_order_status("")

        assert "error" in result
        assert "suggestion" in result
