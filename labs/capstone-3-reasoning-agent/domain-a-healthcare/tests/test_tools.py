"""
Tests for Healthcare Pre-Authorization Decision Support Agent tools.

Run from the domain-a-healthcare directory:
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
    lookup_clinical_criteria,
    verify_diagnosis_match,
    check_network_status,
    get_benefit_summary,
    generate_auth_recommendation,
    execute_tool,
)
from mock_data import CLINICAL_CRITERIA, PROVIDER_NETWORK, FACILITIES, BENEFIT_PLANS


# -----------------------------------------------------------------------
# lookup_clinical_criteria
# -----------------------------------------------------------------------

class TestLookupClinicalCriteria:
    def test_known_cpt_code_returns_criteria(self):
        """CPT 27447 (Total Knee Arthroplasty) should return full criteria."""
        result = lookup_clinical_criteria("27447")
        assert "error" not in result
        assert result["cpt_code"] == "27447"
        assert result["procedure_name"] == "Total Knee Arthroplasty (TKA)"
        assert result["category"] == "Orthopedic Surgery"
        assert "M17.11" in result["required_diagnoses"]
        assert len(result["criteria"]) >= 3
        assert result["approval_validity_days"] == 90

    def test_another_known_cpt_code(self):
        """CPT 29881 (Knee Arthroscopy) should also return criteria."""
        result = lookup_clinical_criteria("29881")
        assert result["procedure_name"] == "Knee Arthroscopy with Meniscectomy"
        assert "M23.21" in result["required_diagnoses"]

    def test_unknown_cpt_code_returns_error(self):
        """An unknown CPT code should return an error dict."""
        result = lookup_clinical_criteria("00000")
        assert "error" in result
        assert "00000" in result["error"]

    def test_experimental_procedure(self):
        """CPT 99999 (experimental) should return criteria with special flags."""
        result = lookup_clinical_criteria("99999")
        assert result["procedure_name"] == "Experimental Regenerative Cartilage Implant"
        assert result["category"] == "Experimental / Investigational"
        assert result["approval_validity_days"] == 0
        assert result["peer_review_threshold"] == "medical_director_review_required"


# -----------------------------------------------------------------------
# verify_diagnosis_match
# -----------------------------------------------------------------------

class TestVerifyDiagnosisMatch:
    def test_matching_diagnosis(self):
        """M17.11 is a valid diagnosis for CPT 27447 — should match."""
        result = verify_diagnosis_match("27447", ["M17.11"])
        assert result["match"] is True
        assert "M17.11" in result["matched_codes"]
        assert result["unmatched_codes"] == []
        assert result["procedure_name"] == "Total Knee Arthroplasty (TKA)"
        assert "M17.11" in result["details"]

    def test_non_matching_diagnosis(self):
        """Z99.99 is not a valid diagnosis for CPT 27447 — should not match."""
        result = verify_diagnosis_match("27447", ["Z99.99"])
        assert result["match"] is False
        assert result["matched_codes"] == []
        assert "Z99.99" in result["unmatched_codes"]

    def test_mixed_matching_and_non_matching(self):
        """Some codes match, some do not."""
        result = verify_diagnosis_match("27447", ["M17.11", "Z99.99"])
        assert result["match"] is True
        assert "M17.11" in result["matched_codes"]
        assert "Z99.99" in result["unmatched_codes"]

    def test_multiple_matching_diagnoses(self):
        """Multiple valid codes should all appear in matched_codes."""
        result = verify_diagnosis_match("27447", ["M17.0", "M17.11"])
        assert result["match"] is True
        assert len(result["matched_codes"]) == 2

    def test_unknown_cpt_returns_error(self):
        """Unknown CPT should return an error."""
        result = verify_diagnosis_match("00000", ["M17.11"])
        assert "error" in result


# -----------------------------------------------------------------------
# check_network_status
# -----------------------------------------------------------------------

class TestCheckNetworkStatus:
    def test_in_network_provider_and_facility(self):
        """Dr. Chen (in-network) + Valley Medical (in-network) + PPO Gold."""
        result = check_network_status("NPI-1234567890", "FAC-001", "PLAN-PPO-GOLD")
        assert result["combined_status"] == "in_network"
        assert result["provider"]["name"] == "Dr. Sarah Chen"
        assert result["provider"]["network_tier"] == "preferred"
        assert result["facility"]["name"] == "Valley Medical Center"
        assert result["plan_type"] == "PPO"

    def test_out_of_network_provider_ppo(self):
        """Dr. Morton (out-of-network) + Summit (out-of-network) under PPO."""
        result = check_network_status("NPI-9876543210", "FAC-005", "PLAN-PPO-GOLD")
        assert result["combined_status"] == "out_of_network"
        assert "out-of-network" in result["status_detail"].lower() or "out_of_network" in result["status_detail"].lower()

    def test_out_of_network_hmo_not_covered(self):
        """Out-of-network under HMO should return 'not_covered'."""
        result = check_network_status("NPI-9876543210", "FAC-005", "PLAN-HMO-BASIC")
        assert result["combined_status"] == "not_covered"
        assert "hmo" in result["status_detail"].lower()

    def test_unknown_provider_returns_error(self):
        """Unknown NPI should return an error."""
        result = check_network_status("NPI-0000000000", "FAC-001", "PLAN-PPO-GOLD")
        assert "error" in result

    def test_unknown_facility_returns_error(self):
        """Unknown facility should return an error."""
        result = check_network_status("NPI-1234567890", "FAC-999", "PLAN-PPO-GOLD")
        assert "error" in result

    def test_unknown_plan_returns_error(self):
        """Unknown plan should return an error."""
        result = check_network_status("NPI-1234567890", "FAC-001", "PLAN-UNKNOWN")
        assert "error" in result


# -----------------------------------------------------------------------
# get_benefit_summary
# -----------------------------------------------------------------------

class TestGetBenefitSummary:
    def test_covered_category_ppo_gold(self):
        """Orthopedic Surgery under PPO Gold should be covered."""
        result = get_benefit_summary("PLAN-PPO-GOLD", "Orthopedic Surgery")
        assert result["category_covered"] is True
        assert result["category_excluded"] is False
        assert result["plan_name"] == "PPO Gold Plus"
        assert result["plan_type"] == "PPO"
        assert result["in_network"]["deductible"] == 500
        assert result["in_network"]["deductible_met"] == 500
        assert result["in_network"]["remaining_deductible"] == 0
        assert result["in_network"]["coinsurance"] == "10%"
        assert result["pre_auth_required"] is True

    def test_ppo_gold_has_oon_benefits(self):
        """PPO Gold should include out-of-network benefit details."""
        result = get_benefit_summary("PLAN-PPO-GOLD", "Orthopedic Surgery")
        assert "out_of_network" in result
        assert result["out_of_network"]["deductible"] == 2000
        assert result["out_of_network"]["coinsurance"] == "40%"

    def test_excluded_category(self):
        """Experimental / Investigational should be excluded."""
        result = get_benefit_summary("PLAN-PPO-GOLD", "Experimental / Investigational")
        assert result["category_covered"] is False
        assert result["category_excluded"] is True
        assert "exclusion_note" in result

    def test_hmo_plan_has_annual_max(self):
        """HMO Basic has an annual max of $250,000."""
        result = get_benefit_summary("PLAN-HMO-BASIC", "Orthopedic Surgery")
        assert result["plan_type"] == "HMO"
        assert result.get("annual_max") == 250000

    def test_unknown_plan_returns_error(self):
        """Unknown plan should return an error."""
        result = get_benefit_summary("PLAN-UNKNOWN", "Orthopedic Surgery")
        assert "error" in result


# -----------------------------------------------------------------------
# generate_auth_recommendation
# -----------------------------------------------------------------------

class TestGenerateAuthRecommendation:
    def test_all_criteria_met_in_network_approved(self):
        """All criteria met + in-network should be APPROVED."""
        result = generate_auth_recommendation(
            cpt_code="27447",
            diagnosis_match=True,
            network_status="in_network",
            benefit_covered=True,
            clinical_notes_summary="All criteria met, KL grade 3, WOMAC 52.",
        )
        assert result["recommendation"] == "APPROVED"
        assert result["approval_validity_days"] == 90
        assert result["peer_review_required"] is False
        assert "All criteria met" in result["reason"] or "All clinical criteria" in result["reason"]

    def test_diagnosis_not_matched_pended(self):
        """Diagnosis mismatch should result in PENDED for peer review."""
        result = generate_auth_recommendation(
            cpt_code="27447",
            diagnosis_match=False,
            network_status="in_network",
            benefit_covered=True,
            clinical_notes_summary="Diagnosis codes do not match.",
        )
        assert result["recommendation"] == "PENDED"
        assert result["peer_review_required"] is True

    def test_benefit_not_covered_denied(self):
        """Excluded benefit category should be DENIED."""
        result = generate_auth_recommendation(
            cpt_code="99999",
            diagnosis_match=True,
            network_status="in_network",
            benefit_covered=False,
            clinical_notes_summary="Experimental procedure.",
        )
        assert result["recommendation"] == "DENIED"
        assert result["approval_validity_days"] == 0

    def test_hmo_out_of_network_denied(self):
        """not_covered network status (HMO OON) should be DENIED."""
        result = generate_auth_recommendation(
            cpt_code="27447",
            diagnosis_match=True,
            network_status="not_covered",
            benefit_covered=True,
            clinical_notes_summary="HMO out-of-network request.",
        )
        assert result["recommendation"] == "DENIED"
        assert "in-network" in result["reason"].lower() or "out-of-network" in result["reason"].lower()

    def test_out_of_network_ppo_approved_with_conditions(self):
        """Out-of-network under PPO should be APPROVED with OON conditions."""
        result = generate_auth_recommendation(
            cpt_code="27447",
            diagnosis_match=True,
            network_status="out_of_network",
            benefit_covered=True,
            clinical_notes_summary="Criteria met, OON provider.",
        )
        assert result["recommendation"] == "APPROVED"
        assert result["approval_validity_days"] == 90
        assert any("out-of-network" in c.lower() for c in result["conditions"])


# -----------------------------------------------------------------------
# execute_tool dispatcher
# -----------------------------------------------------------------------

class TestExecuteTool:
    def test_dispatch_known_tool(self):
        """execute_tool should dispatch to lookup_clinical_criteria."""
        raw = execute_tool("lookup_clinical_criteria", {"cpt_code": "27447"})
        result = json.loads(raw)
        assert result["cpt_code"] == "27447"

    def test_dispatch_unknown_tool(self):
        """execute_tool should return an error for unknown tool names."""
        raw = execute_tool("nonexistent_tool", {})
        result = json.loads(raw)
        assert "error" in result
        assert "Unknown tool" in result["error"]
