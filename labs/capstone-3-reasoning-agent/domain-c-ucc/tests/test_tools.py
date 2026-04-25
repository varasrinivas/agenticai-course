"""
Tests for UCC Entity Resolution Agent tools.

Run from the domain-c-ucc directory:
    python -m pytest tests/

These tests exercise the tool functions directly using mock data.
No API key or network access is required.
"""

import sys
import os
import json

# Add the solution directory to the path so we can import tools and mock_data
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "solution"))

from tools import (
    search_filings_by_name,
    fuzzy_match_score,
    get_filing_details,
    get_business_registry_data,
    merge_entity_profile,
    execute_tool,
)
from mock_data import UCC_FILINGS, BUSINESS_REGISTRY


# -----------------------------------------------------------------------
# search_filings_by_name
# -----------------------------------------------------------------------

class TestSearchFilingsByName:
    def test_acme_returns_multiple_results(self):
        """Searching 'Acme Corp' should find filings across multiple states."""
        result = search_filings_by_name("Acme Corp")
        assert result["query"] == "Acme Corp"
        assert result["results_count"] >= 5
        # Should find filings in at least CA, TX, DE
        states_found = {r["state"] for r in result["results"]}
        assert "CA" in states_found
        assert "TX" in states_found
        assert "DE" in states_found

    def test_acme_results_include_name_variations(self):
        """Results should include name variations like 'ACME CORPORATION'."""
        result = search_filings_by_name("Acme Corp")
        debtor_names = {r["debtor_name"] for r in result["results"]}
        # Should find at least the exact match and the corporation variant
        assert "Acme Corp" in debtor_names
        assert "ACME CORPORATION" in debtor_names or "Acme Corporation" in debtor_names

    def test_search_limited_to_state(self):
        """Search limited to CA should only return CA filings."""
        result = search_filings_by_name("Acme Corp", state="CA")
        assert all(r["state"] == "CA" for r in result["results"])
        assert result["results_count"] >= 2

    def test_pinnacle_search(self):
        """Searching 'Pinnacle Systems' should find filings in multiple states."""
        result = search_filings_by_name("Pinnacle Systems")
        assert result["results_count"] >= 1
        # Should find the Pinnacle Systems International filings
        filing_numbers = {r["filing_number"] for r in result["results"]}
        assert "CA-2022-0553192" in filing_numbers or any(
            "Pinnacle" in r["debtor_name"] for r in result["results"]
        )

    def test_no_results_for_unknown_name(self):
        """A completely unknown name should return zero results."""
        result = search_filings_by_name("Zzyzx Nonexistent Corp")
        assert result["results_count"] == 0
        assert result["results"] == []

    def test_results_include_ein(self):
        """Each result should include the debtor EIN when available."""
        result = search_filings_by_name("Acme Corp")
        acme_results = [r for r in result["results"] if r["debtor_ein"] == "94-3829471"]
        assert len(acme_results) >= 3


# -----------------------------------------------------------------------
# fuzzy_match_score
# -----------------------------------------------------------------------

class TestFuzzyMatchScore:
    def test_exact_match_returns_1_0(self):
        """Identical names (after normalization) should return score 1.0."""
        result = fuzzy_match_score("Acme Corp", "ACME CORP")
        assert result["score"] == 1.0
        assert result["match_type"] == "exact"

    def test_abbreviation_match_returns_high_score(self):
        """'Acme Corp' vs 'ACME CORPORATION' should match via abbreviation."""
        result = fuzzy_match_score("Acme Corp", "ACME CORPORATION")
        assert result["score"] >= 0.85
        assert result["match_type"] in ("abbreviation", "substring")

    def test_substring_match(self):
        """One name contained in the other should get a high score."""
        result = fuzzy_match_score("Acme Corp", "Acme Corp dba AcmeTech Solutions")
        assert result["score"] >= 0.80
        assert result["match_type"] in ("substring", "abbreviation")

    def test_low_match_different_names(self):
        """Completely different names should get a low score."""
        result = fuzzy_match_score("Acme Corp", "Pinnacle Systems International")
        assert result["score"] < 0.5

    def test_acme_vs_acme_holdings_low_match(self):
        """'Acme Corp' vs 'Acme Holdings LLC' should be a low match (different entity)."""
        result = fuzzy_match_score("Acme Corp", "Acme Holdings LLC")
        assert result["score"] < 0.5

    def test_pinnacle_abbreviation_match(self):
        """'Pinnacle Systems Intl' vs 'Pinnacle Systems International' should match."""
        result = fuzzy_match_score("Pinnacle Systems Intl", "Pinnacle Systems International")
        assert result["score"] >= 0.80


# -----------------------------------------------------------------------
# get_filing_details
# -----------------------------------------------------------------------

class TestGetFilingDetails:
    def test_known_filing(self):
        """CA-2023-0847291 should return full filing details."""
        result = get_filing_details("CA-2023-0847291", "CA")
        assert "error" not in result
        assert result["filing_number"] == "CA-2023-0847291"
        assert result["state"] == "CA"
        assert result["debtor_name"] == "Acme Corp"
        assert result["debtor_ein"] == "94-3829471"
        assert result["secured_party"] == "Pacific Commerce Bank"
        assert result["status"] == "active"

    def test_filing_with_amendments(self):
        """CA-2022-0553192 should include amendment data."""
        result = get_filing_details("CA-2022-0553192", "CA")
        assert len(result["amendments"]) >= 1
        assert result["amendments"][0]["type"] == "collateral_change"

    def test_de_filing_with_name_change_amendment(self):
        """DE-2021-0091447 should have a debtor name change amendment."""
        result = get_filing_details("DE-2021-0091447", "DE")
        assert result["debtor_name"] == "Acme Corp"
        assert len(result["amendments"]) >= 1
        assert result["amendments"][0]["type"] == "debtor_name_change"

    def test_unknown_filing_returns_error(self):
        """Unknown filing number should return an error."""
        result = get_filing_details("XX-0000-0000000", "CA")
        assert "error" in result

    def test_unknown_state_returns_error(self):
        """Unknown state should return an error."""
        result = get_filing_details("CA-2023-0847291", "ZZ")
        assert "error" in result


# -----------------------------------------------------------------------
# get_business_registry_data
# -----------------------------------------------------------------------

class TestGetBusinessRegistryData:
    def test_lookup_by_ein(self):
        """EIN 94-3829471 should return Acme Corporation registry data."""
        result = get_business_registry_data(ein="94-3829471")
        assert "error" not in result
        assert result["legal_name"] == "Acme Corporation"
        assert result["ein"] == "94-3829471"
        assert "Acme Corp" in result["dba_names"]
        assert "AcmeTech Solutions" in result["dba_names"]
        assert result["entity_type"] == "Corporation"
        assert result["state_of_incorporation"] == "DE"
        assert len(result["officers"]) >= 3

    def test_lookup_by_name(self):
        """Looking up 'Acme Corporation' by name should find it."""
        result = get_business_registry_data(business_name="Acme Corporation")
        assert result["ein"] == "94-3829471"

    def test_lookup_by_dba_name(self):
        """Looking up a DBA name should also find the entity."""
        result = get_business_registry_data(business_name="AcmeTech Solutions")
        assert result["ein"] == "94-3829471"

    def test_acme_holdings_separate_entity(self):
        """Acme Holdings LLC has a different EIN and is a holding company."""
        result = get_business_registry_data(ein="94-5501287")
        assert result["legal_name"] == "Acme Holdings LLC"
        assert result["entity_type"] == "LLC"
        assert result["officers"][0]["name"] == "Robert Chen"
        assert "Parent holding company" in result.get("notes", "")

    def test_trident_formerly_pinnacle_transport(self):
        """Trident Logistics should show former name Pinnacle Transport Services."""
        result = get_business_registry_data(ein="51-0482193")
        assert result["legal_name"] == "Trident Logistics Group LLC"
        assert "Pinnacle Transport Services" in result["dba_names"]

    def test_unknown_ein_returns_error(self):
        """Unknown EIN should return an error."""
        result = get_business_registry_data(ein="00-0000000")
        assert "error" in result

    def test_unknown_name_returns_error(self):
        """Unknown business name should return an error."""
        result = get_business_registry_data(business_name="Zzyzx Nonexistent Corp")
        assert "error" in result

    def test_no_params_returns_error(self):
        """Calling with no params should return an error."""
        result = get_business_registry_data()
        assert "error" in result


# -----------------------------------------------------------------------
# merge_entity_profile
# -----------------------------------------------------------------------

class TestMergeEntityProfile:
    def test_builds_valid_profile(self):
        """Should produce a complete entity profile with expected structure."""
        result = merge_entity_profile(
            entity_name="Acme Corporation",
            ein="94-3829471",
            name_variations=["Acme Corp", "ACME CORPORATION", "Acme Corp dba AcmeTech Solutions"],
            filing_numbers=[
                "CA-2023-0847291", "CA-2024-0112834", "CA-2021-0289451",
                "NV-2023-0034521", "TX-2022-1847592", "TX-2024-0229183",
                "NY-2023-0558291", "DE-2021-0091447",
            ],
            states_with_filings=["CA", "NV", "TX", "NY", "DE"],
            total_secured_parties=8,
            risk_notes="High lien exposure across 5 states.",
        )
        assert result["entity_name"] == "Acme Corporation"
        assert result["ein"] == "94-3829471"
        assert result["profile_status"] == "resolved"
        assert result["filing_summary"]["total_filings"] == 8
        assert result["filing_summary"]["active_filings"] >= 1
        assert set(result["filing_summary"]["states"]) == {"CA", "NV", "TX", "NY", "DE"}

    def test_high_risk_level(self):
        """8 secured parties should result in high risk level."""
        result = merge_entity_profile(
            entity_name="Test Entity",
            ein="00-0000000",
            name_variations=["Test"],
            filing_numbers=["F1", "F2"],
            states_with_filings=["CA"],
            total_secured_parties=8,
            risk_notes="Many lenders.",
        )
        assert result["lien_exposure"]["risk_level"] == "high"

    def test_moderate_risk_level(self):
        """3-4 secured parties should result in moderate risk level."""
        result = merge_entity_profile(
            entity_name="Test Entity",
            ein="00-0000000",
            name_variations=["Test"],
            filing_numbers=["F1"],
            states_with_filings=["CA"],
            total_secured_parties=3,
            risk_notes="Some lenders.",
        )
        assert result["lien_exposure"]["risk_level"] == "moderate"

    def test_low_risk_level(self):
        """1-2 secured parties should result in low risk level."""
        result = merge_entity_profile(
            entity_name="Test Entity",
            ein="00-0000000",
            name_variations=["Test"],
            filing_numbers=["F1"],
            states_with_filings=["CA"],
            total_secured_parties=2,
            risk_notes="Few lenders.",
        )
        assert result["lien_exposure"]["risk_level"] == "low"

    def test_high_confidence_for_many_data_points(self):
        """Many data points should yield confidence >= 0.95."""
        result = merge_entity_profile(
            entity_name="Acme Corporation",
            ein="94-3829471",
            name_variations=["A", "B", "C", "D"],
            filing_numbers=["F1", "F2", "F3", "F4", "F5"],
            states_with_filings=["CA", "NV", "TX"],
            total_secured_parties=5,
            risk_notes="Well documented.",
        )
        # 5 filings + 4 variations + 3 states = 12 data points >= 10
        assert result["confidence_score"] == 0.95

    def test_low_confidence_for_few_data_points(self):
        """Few data points should yield lower confidence."""
        result = merge_entity_profile(
            entity_name="Test",
            ein="00-0000000",
            name_variations=["Test"],
            filing_numbers=["F1"],
            states_with_filings=["CA"],
            total_secured_parties=1,
            risk_notes="Minimal data.",
        )
        # 1 filing + 1 variation + 1 state = 3 data points < 6
        assert result["confidence_score"] == 0.70


# -----------------------------------------------------------------------
# execute_tool dispatcher
# -----------------------------------------------------------------------

class TestExecuteTool:
    def test_dispatch_search_filings(self):
        """execute_tool should dispatch to search_filings_by_name."""
        raw = execute_tool("search_filings_by_name", {"business_name": "Acme Corp"})
        result = json.loads(raw)
        assert result["results_count"] >= 5

    def test_dispatch_unknown_tool(self):
        """execute_tool should return an error for unknown tool names."""
        raw = execute_tool("nonexistent_tool", {})
        result = json.loads(raw)
        assert "error" in result
        assert "Unknown tool" in result["error"]
