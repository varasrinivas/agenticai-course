"""
Tests for the Healthcare Pre-Auth Pipeline — Domain A.

Validates PipelineState initialization, agent instantiation, circuit breaker
integration, mock data structure, and a simulated happy-path pipeline run
(without calling the Anthropic API).
"""

import os
import sys
from datetime import datetime
from unittest.mock import patch, MagicMock

import pytest

SOLUTION_DIR = os.path.join(os.path.dirname(__file__), "..", "solution")
sys.path.insert(0, SOLUTION_DIR)

from agents import PipelineState, IntakeResult, CriteriaResult, DecisionResult, CommunicationResult
from agents.agent1 import IntakeAgent, validate_request, extract_clinical_info, check_eligibility
from agents.agent2 import ClinicalCriteriaAgent, lookup_clinical_criteria, match_diagnosis_to_criteria, calculate_medical_necessity_score
from agents.agent3 import DecisionAgent, apply_decision_rules, generate_determination
from agents.agent4 import CommunicationAgent, draft_notification, format_letter, log_communication
from quality_gate import CircuitBreaker
from mock_data import PREAUTH_REQUESTS, CLINICAL_CRITERIA, PROVIDER_NETWORK, BENEFIT_PLANS, ELIGIBILITY


# ---------------------------------------------------------------------------
# PipelineState initialization
# ---------------------------------------------------------------------------
class TestPipelineState:
    def test_default_state(self):
        state = PipelineState()
        assert state.pipeline_id == ""
        assert state.halted is False
        assert state.completed is False
        assert isinstance(state.intake, IntakeResult)
        assert isinstance(state.criteria, CriteriaResult)
        assert isinstance(state.decision, DecisionResult)
        assert isinstance(state.communication, CommunicationResult)

    def test_state_with_values(self):
        state = PipelineState(
            pipeline_id="PL-TEST",
            started_at="2024-11-20T10:00:00",
            halted=False,
        )
        assert state.pipeline_id == "PL-TEST"
        assert state.started_at == "2024-11-20T10:00:00"

    def test_agent_trace_starts_empty(self):
        state = PipelineState()
        assert state.agent_trace == []

    def test_raw_request_starts_empty(self):
        state = PipelineState()
        assert state.raw_request == {}


# ---------------------------------------------------------------------------
# Agent instantiation
# ---------------------------------------------------------------------------
class TestAgentInstantiation:
    def test_intake_agent(self):
        agent = IntakeAgent()
        assert agent.name == "IntakeAgent"
        assert len(agent.tool_schemas) > 0

    def test_clinical_criteria_agent(self):
        agent = ClinicalCriteriaAgent()
        assert agent.name == "ClinicalCriteriaAgent"
        assert len(agent.tool_schemas) > 0

    def test_decision_agent(self):
        agent = DecisionAgent()
        assert agent.name == "DecisionAgent"
        assert len(agent.tool_schemas) > 0

    def test_communication_agent(self):
        agent = CommunicationAgent()
        assert agent.name == "CommunicationAgent"
        assert len(agent.tool_schemas) > 0


# ---------------------------------------------------------------------------
# Mock data is well-formed
# ---------------------------------------------------------------------------
class TestMockData:
    def test_preauth_requests_not_empty(self):
        assert len(PREAUTH_REQUESTS) > 0

    def test_preauth_requests_has_expected_keys(self):
        assert "PA-2024-001" in PREAUTH_REQUESTS
        assert "PA-2024-009" in PREAUTH_REQUESTS  # invalid CPT edge case
        assert "PA-2024-012" in PREAUTH_REQUESTS  # HITL borderline case

    def test_request_structure(self):
        req = PREAUTH_REQUESTS["PA-2024-001"]
        required_fields = [
            "request_id", "patient_name", "patient_dob", "patient_id",
            "plan_id", "provider_npi", "cpt_code", "diagnosis_codes",
            "clinical_notes", "urgency", "submitted_date",
        ]
        for field in required_fields:
            assert field in req, f"Missing field: {field}"

    def test_clinical_criteria_has_entries(self):
        assert len(CLINICAL_CRITERIA) > 0
        assert "27447" in CLINICAL_CRITERIA  # TKA

    def test_provider_network_has_entries(self):
        assert len(PROVIDER_NETWORK) > 0
        assert "NPI-1234567890" in PROVIDER_NETWORK

    def test_benefit_plans_has_entries(self):
        assert len(BENEFIT_PLANS) > 0
        assert "PLAN-PPO-GOLD" in BENEFIT_PLANS

    def test_eligibility_has_entries(self):
        assert len(ELIGIBILITY) > 0
        assert "PT-90001" in ELIGIBILITY


# ---------------------------------------------------------------------------
# Tool functions (unit tests, no API calls)
# ---------------------------------------------------------------------------
class TestIntakeTools:
    def test_validate_request_valid(self):
        result = validate_request("PA-2024-001")
        assert result["valid"] is True
        assert result["errors"] == []

    def test_validate_request_invalid_cpt(self):
        result = validate_request("PA-2024-009")
        assert result["valid"] is False
        assert any("Unknown CPT" in e or "INVALID" in e for e in result["errors"])

    def test_validate_request_missing_diagnosis(self):
        result = validate_request("PA-2024-010")
        assert result["valid"] is False
        assert any("diagnosis" in e.lower() for e in result["errors"])

    def test_validate_request_not_found(self):
        result = validate_request("NONEXISTENT")
        assert result["valid"] is False

    def test_extract_clinical_info_happy(self):
        result = extract_clinical_info("PA-2024-001")
        info = result["clinical_info"]
        assert info["womac_score"] == 52
        assert info["kl_grade"] == 3
        assert info["bmi"] == pytest.approx(32.1)

    def test_check_eligibility_found(self):
        result = check_eligibility("PT-90001")
        assert result["eligible"] is True

    def test_check_eligibility_not_found(self):
        result = check_eligibility("PT-NONEXISTENT")
        assert result["eligible"] is False


class TestCriteriaTools:
    def test_lookup_criteria_found(self):
        result = lookup_clinical_criteria("27447")
        assert result["procedure_name"] == "Total Knee Arthroplasty (TKA)"

    def test_lookup_criteria_not_found(self):
        result = lookup_clinical_criteria("00000")
        assert "error" in result

    def test_match_diagnosis_match(self):
        result = match_diagnosis_to_criteria("27447", ["M17.11"])
        assert result["match"] is True
        assert "M17.11" in result["matched_codes"]

    def test_match_diagnosis_no_match(self):
        result = match_diagnosis_to_criteria("27447", ["Z96.651"])
        assert result["match"] is False

    def test_medical_necessity_score_high(self):
        clinical_info = {
            "conservative_treatment_months": 6,
            "kl_grade": 3,
            "womac_score": 52,
            "bmi": 32.1,
            "urgency_indicators": [],
        }
        result = calculate_medical_necessity_score("27447", clinical_info, True)
        assert result["total_score"] >= 80


class TestDecisionTools:
    def test_approve_high_score_in_network(self):
        result = apply_decision_rules(
            cpt_code="27447",
            diagnosis_match=True,
            medical_necessity_score=90.0,
            network_status="in_network",
            benefit_covered=True,
            plan_type="PPO",
        )
        assert result["decision"] == "APPROVED"

    def test_deny_excluded_benefit(self):
        result = apply_decision_rules(
            cpt_code="99999",
            diagnosis_match=True,
            medical_necessity_score=50.0,
            network_status="in_network",
            benefit_covered=False,
            plan_type="PPO",
        )
        assert result["decision"] == "DENIED"

    def test_generate_determination_approved(self):
        det = generate_determination("APPROVED", 90.0, "All criteria met", "27447")
        assert det["determination"] == "APPROVED"
        assert det["approval_validity_days"] == 90


class TestCommunicationTools:
    def test_draft_notification(self):
        result = draft_notification("PA-2024-001", "APPROVED", "All criteria met")
        assert "APPROVED" in result["content"]
        assert result["request_id"] == "PA-2024-001"

    def test_format_letter_approval(self):
        result = format_letter("PA-2024-001", "approval")
        assert "APPROVED" in result["letter_text"]

    def test_log_communication(self):
        result = log_communication("PA-2024-001", "approval", "Maria Gonzalez", "mail")
        assert result["logged"] is True
        assert result["entry"]["request_id"] == "PA-2024-001"


# ---------------------------------------------------------------------------
# CircuitBreaker integration with coordinator
# ---------------------------------------------------------------------------
class TestCircuitBreakerIntegration:
    def test_breaker_tracks_failures(self):
        cb = CircuitBreaker(name="test", failure_threshold=0.50, window_size=4)
        cb.record_failure()
        cb.record_failure()
        assert cb.failure_rate == pytest.approx(1.0)

    def test_breaker_trips_at_threshold(self):
        cb = CircuitBreaker(name="test", failure_threshold=0.10, window_size=20)
        # Record 3 consecutive failures (100% > 10%)
        cb.record_failure()
        cb.record_failure()
        cb.record_failure()
        assert cb.is_tripped() is True


# ---------------------------------------------------------------------------
# Pipeline end-to-end (mocking Anthropic API)
# ---------------------------------------------------------------------------
class TestPipelineRun:
    @patch("agents.agent1.anthropic.Anthropic")
    @patch("agents.agent2.anthropic.Anthropic")
    @patch("agents.agent3.anthropic.Anthropic")
    @patch("agents.agent4.anthropic.Anthropic")
    def test_run_pipeline_happy_path(self, mock_a4, mock_a3, mock_a2, mock_a1):
        """Mock all Anthropic calls and run the pipeline for PA-2024-001."""
        # Create a mock response that signals end_turn immediately
        mock_response = MagicMock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [MagicMock(type="text", text="Done.")]

        for mock_cls in [mock_a1, mock_a2, mock_a3, mock_a4]:
            mock_cls.return_value.messages.create.return_value = mock_response

        # Patch input() for the HITL gate in DecisionAgent
        with patch("builtins.input", return_value="a"):
            import coordinator
            coordinator._circuit_breaker.reset()
            state = coordinator.run_pipeline("PA-2024-001")

        assert state.halted is False
        assert state.completed is True
        assert state.decision.determination in ("APPROVED", "DENIED", "PENDED")
        assert state.communication.communication_logged is True

    def test_run_pipeline_not_found(self):
        """run_pipeline with a non-existent request returns halted state."""
        import coordinator
        coordinator._circuit_breaker.reset()
        state = coordinator.run_pipeline("NONEXISTENT")
        assert state.halted is True
        assert "not found" in state.halt_reason.lower()
