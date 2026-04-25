"""
M15B — Tool Unit Tests
=======================
Tests the 3 tools WITHOUT making any API calls.
Run from the M15B-build-complete-agent directory:
    python -m pytest tests/test_tools.py -v
"""

import json
import sys
import os

# Add solution dir to path so we can import the tools
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "solution"))

from tools import (
    tool_search_filings,
    tool_get_filing_details,
    tool_calculate_risk_score,
    execute_tool,
    TOOL_DEFINITIONS,
)
from mock_data import MOCK_FILINGS, get_stats


# =============================================================================
# DATA INTEGRITY TESTS
# =============================================================================

class TestMockData:
    """Verify the mock data is complete and consistent."""

    def test_has_15_filings(self):
        assert len(MOCK_FILINGS) == 15, f"Expected 15 filings, got {len(MOCK_FILINGS)}"

    def test_covers_5_states(self):
        states = set(f["state"] for f in MOCK_FILINGS)
        expected = {"New York", "California", "Texas", "Florida", "Illinois"}
        assert states == expected, f"Expected {expected}, got {states}"

    def test_has_acme_in_all_states(self):
        """Acme Corporation should appear in all 5 states for cross-state research."""
        acme_states = set(f["state"] for f in MOCK_FILINGS if "acme" in f["debtor"]["name"].lower())
        expected = {"New York", "California", "Texas", "Florida", "Illinois"}
        assert acme_states == expected, f"Acme found in {acme_states}, expected {expected}"

    def test_has_amendments(self):
        amendments = [f for f in MOCK_FILINGS if f["type"] == "UCC-3"]
        assert len(amendments) >= 3, f"Expected >= 3 amendments, got {len(amendments)}"

    def test_has_terminated_filing(self):
        terminated = [f for f in MOCK_FILINGS if f["status"] == "Terminated"]
        assert len(terminated) >= 1, "Expected at least 1 terminated filing"

    def test_all_filings_have_required_fields(self):
        required = ["filing_number", "type", "state", "filing_date", "status", "debtor", "secured_party", "collateral_description"]
        for f in MOCK_FILINGS:
            for field in required:
                assert field in f, f"Filing {f.get('filing_number', '?')} missing field: {field}"

    def test_debtors_have_name(self):
        for f in MOCK_FILINGS:
            assert f["debtor"]["name"], f"Filing {f['filing_number']} has empty debtor name"


# =============================================================================
# TOOL: search_filings
# =============================================================================

class TestSearchFilings:
    """Test the search_filings tool."""

    def test_search_by_debtor_name(self):
        result = json.loads(tool_search_filings(debtor_name="Acme"))
        assert isinstance(result, list), "Expected list result"
        assert len(result) >= 5, f"Acme should have >= 5 filings, got {len(result)}"

    def test_search_by_state(self):
        result = json.loads(tool_search_filings(state="Texas"))
        assert isinstance(result, list)
        assert len(result) == 3, f"Texas should have 3 filings, got {len(result)}"
        for f in result:
            assert f["state"] == "Texas"

    def test_search_by_name_and_state(self):
        result = json.loads(tool_search_filings(debtor_name="Acme", state="New York"))
        assert isinstance(result, list)
        assert len(result) == 2, f"Acme in NY should have 2 filings, got {len(result)}"

    def test_search_no_results(self):
        result = json.loads(tool_search_filings(debtor_name="NonExistent Corp"))
        # Should return a message, not crash
        assert "message" in result or isinstance(result, list)

    def test_search_case_insensitive(self):
        result = json.loads(tool_search_filings(debtor_name="acme"))
        assert isinstance(result, list)
        assert len(result) >= 5

    def test_search_partial_name(self):
        result = json.loads(tool_search_filings(debtor_name="Lone Star"))
        assert isinstance(result, list)
        assert len(result) >= 2

    def test_result_has_required_fields(self):
        result = json.loads(tool_search_filings(debtor_name="Acme"))
        for f in result:
            assert "filing_number" in f
            assert "debtor" in f
            assert "secured_party" in f
            assert "state" in f
            assert "status" in f


# =============================================================================
# TOOL: get_filing_details
# =============================================================================

class TestGetFilingDetails:
    """Test the get_filing_details tool."""

    def test_get_existing_filing(self):
        result = json.loads(tool_get_filing_details("UCC-2024-NY-0012847"))
        assert "filing_number" in result
        assert result["filing_number"] == "UCC-2024-NY-0012847"
        assert "collateral_description" in result

    def test_get_nonexistent_filing(self):
        result = json.loads(tool_get_filing_details("UCC-9999-XX-0000000"))
        assert "error" in result

    def test_get_amendment_filing(self):
        result = json.loads(tool_get_filing_details("UCC-2024-FL-0054219"))
        assert result["type"] == "UCC-3"
        assert result["status"] == "Amendment"

    def test_get_terminated_filing(self):
        result = json.loads(tool_get_filing_details("UCC-2023-NY-0145678"))
        assert result["status"] == "Terminated"


# =============================================================================
# TOOL: calculate_risk_score
# =============================================================================

class TestCalculateRiskScore:
    """Test the calculate_risk_score tool."""

    def test_acme_high_risk(self):
        """Acme has 5+ active filings across 5 states — should be HIGH."""
        result = json.loads(tool_calculate_risk_score("Acme Corporation"))
        assert result["risk_level"] == "HIGH", f"Expected HIGH, got {result['risk_level']}"
        assert result["risk_score"] >= 0.7
        assert result["total_filings"] >= 5

    def test_lone_star_lower_risk(self):
        """Lone Star has equipment-specific liens — should be MEDIUM or LOW."""
        result = json.loads(tool_calculate_risk_score("Lone Star Energy"))
        assert result["risk_level"] in ("LOW", "MEDIUM")
        assert result["total_filings"] >= 2

    def test_nonexistent_debtor(self):
        result = json.loads(tool_calculate_risk_score("NonExistent Corp"))
        assert result["risk_level"] == "UNKNOWN"
        assert result["risk_score"] == 0

    def test_risk_has_factors(self):
        result = json.loads(tool_calculate_risk_score("Acme Corporation"))
        assert "factors" in result
        assert isinstance(result["factors"], list)
        assert len(result["factors"]) >= 3

    def test_risk_has_recommendation(self):
        result = json.loads(tool_calculate_risk_score("Acme Corporation"))
        assert "recommendation" in result
        assert len(result["recommendation"]) > 20

    def test_risk_score_capped_at_1(self):
        result = json.loads(tool_calculate_risk_score("Acme Corporation"))
        assert result["risk_score"] <= 1.0


# =============================================================================
# TOOL DISPATCHER
# =============================================================================

class TestExecuteTool:
    """Test the execute_tool dispatcher."""

    def test_routes_search(self):
        result = execute_tool("search_filings", {"debtor_name": "Acme"})
        parsed = json.loads(result)
        assert isinstance(parsed, list)

    def test_routes_details(self):
        result = execute_tool("get_filing_details", {"filing_number": "UCC-2024-NY-0012847"})
        parsed = json.loads(result)
        assert "filing_number" in parsed

    def test_routes_risk(self):
        result = execute_tool("calculate_risk_score", {"debtor_name": "Acme"})
        parsed = json.loads(result)
        assert "risk_score" in parsed

    def test_unknown_tool(self):
        result = execute_tool("nonexistent_tool", {})
        parsed = json.loads(result)
        assert "error" in parsed


# =============================================================================
# TOOL DEFINITIONS
# =============================================================================

class TestToolDefinitions:
    """Verify tool definitions are valid for Claude's API."""

    def test_has_3_tools(self):
        assert len(TOOL_DEFINITIONS) == 3

    def test_tools_have_name_and_schema(self):
        for tool in TOOL_DEFINITIONS:
            assert "name" in tool
            assert "description" in tool
            assert "input_schema" in tool
            assert tool["input_schema"]["type"] == "object"

    def test_tool_names(self):
        names = {t["name"] for t in TOOL_DEFINITIONS}
        assert names == {"search_filings", "get_filing_details", "calculate_risk_score"}
