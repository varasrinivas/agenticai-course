"""
Tests for the UCC Data Engineering Pipeline — Domain C.

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

from agents import (
    PipelineState,
    IngestionResult,
    TransformationResult,
    QualityResult,
    ReportingResult,
)
from agents.agent1 import IngestionAgent
from agents.agent2 import TransformationAgent
from agents.agent3 import QualityAgent
from agents.agent4 import ReportingAgent
from quality_gate import CircuitBreaker
from mock_data import FILING_BATCHES, ENTITY_REGISTRY, COLLATERAL_TYPES, QUALITY_RULES


# ---------------------------------------------------------------------------
# PipelineState initialization
# ---------------------------------------------------------------------------
class TestPipelineState:
    def test_default_state(self):
        state = PipelineState()
        assert state.pipeline_id == ""
        assert state.halted is False
        assert state.completed is False
        assert isinstance(state.ingestion, IngestionResult)
        assert isinstance(state.transformation, TransformationResult)
        assert isinstance(state.quality, QualityResult)
        assert isinstance(state.reporting, ReportingResult)

    def test_state_with_values(self):
        state = PipelineState(
            pipeline_id="PL-TEST",
            started_at="2024-11-20T10:00:00",
        )
        assert state.pipeline_id == "PL-TEST"

    def test_agent_trace_starts_empty(self):
        state = PipelineState()
        assert state.agent_trace == []

    def test_raw_batch_starts_empty(self):
        state = PipelineState()
        assert state.raw_batch == {}


# ---------------------------------------------------------------------------
# Agent instantiation
# ---------------------------------------------------------------------------
class TestAgentInstantiation:
    def test_ingestion_agent(self):
        agent = IngestionAgent()
        assert agent.name == "IngestionAgent"
        assert len(agent.tool_schemas) > 0

    def test_transformation_agent(self):
        agent = TransformationAgent()
        assert agent.name == "TransformationAgent"
        assert len(agent.tool_schemas) > 0

    def test_quality_agent(self):
        agent = QualityAgent()
        assert agent.name == "QualityAgent"
        assert len(agent.tool_schemas) > 0

    def test_reporting_agent(self):
        agent = ReportingAgent()
        assert agent.name == "ReportingAgent"
        assert len(agent.tool_schemas) > 0


# ---------------------------------------------------------------------------
# Mock data is well-formed
# ---------------------------------------------------------------------------
class TestMockData:
    def test_filing_batches_not_empty(self):
        assert len(FILING_BATCHES) > 0

    def test_filing_batches_has_expected_keys(self):
        assert "BATCH-001" in FILING_BATCHES  # happy path (CA CSV)
        assert "BATCH-004" in FILING_BATCHES  # malformed records
        assert "BATCH-009" in FILING_BATCHES  # unsupported xlsx format

    def test_batch_structure(self):
        batch = FILING_BATCHES["BATCH-001"]
        required_fields = ["batch_id", "source", "format", "filing_count", "filings"]
        for field in required_fields:
            assert field in batch, f"Missing field: {field}"

    def test_batch_filings_have_required_fields(self):
        batch = FILING_BATCHES["BATCH-001"]
        for filing in batch["filings"]:
            assert "filing_number" in filing
            assert "debtor_name" in filing
            assert "secured_party" in filing
            assert "collateral" in filing

    def test_filing_count_matches_filings_length(self):
        batch = FILING_BATCHES["BATCH-001"]
        assert batch["filing_count"] == len(batch["filings"])

    def test_entity_registry_has_entries(self):
        assert len(ENTITY_REGISTRY) > 0
        assert "ENT-001" in ENTITY_REGISTRY  # ACME

    def test_entity_has_aliases(self):
        entity = ENTITY_REGISTRY["ENT-001"]
        assert "aliases" in entity
        assert len(entity["aliases"]) > 0
        assert "ACME CORP" in entity["aliases"]

    def test_collateral_types_has_categories(self):
        assert len(COLLATERAL_TYPES) > 0
        assert "inventory" in COLLATERAL_TYPES
        assert "equipment" in COLLATERAL_TYPES
        assert "intellectual_property" in COLLATERAL_TYPES

    def test_quality_rules_has_entries(self):
        assert len(QUALITY_RULES) > 0
        assert "filing_number_required" in QUALITY_RULES
        assert "no_pii_in_collateral" in QUALITY_RULES

    def test_edge_case_malformed_batch(self):
        """BATCH-004 has records with empty debtor_name and empty filing_number."""
        batch = FILING_BATCHES["BATCH-004"]
        filings = batch["filings"]
        assert any(f["debtor_name"] == "" for f in filings)
        assert any(f["filing_number"] == "" for f in filings)

    def test_edge_case_unsupported_format(self):
        """BATCH-009 has xlsx format which is unsupported."""
        batch = FILING_BATCHES["BATCH-009"]
        assert batch["format"] == "xlsx"

    def test_edge_case_pii_in_collateral(self):
        """BATCH-006 has PII (SSN) embedded in collateral description."""
        batch = FILING_BATCHES["BATCH-006"]
        collateral_texts = [f["collateral"] for f in batch["filings"]]
        has_ssn = any("SSN" in c for c in collateral_texts)
        assert has_ssn is True


# ---------------------------------------------------------------------------
# CircuitBreaker integration
# ---------------------------------------------------------------------------
class TestCircuitBreakerIntegration:
    def test_breaker_tracks_failures(self):
        cb = CircuitBreaker(name="test", failure_threshold=0.50, window_size=4)
        cb.record_failure()
        cb.record_failure()
        assert cb.failure_rate == pytest.approx(1.0)

    def test_breaker_trips_at_threshold(self):
        cb = CircuitBreaker(name="test", failure_threshold=0.10, window_size=20)
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
        """Mock all Anthropic calls and run the pipeline for BATCH-001."""
        mock_response = MagicMock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [MagicMock(type="text", text="Done.")]

        for mock_cls in [mock_a1, mock_a2, mock_a3, mock_a4]:
            mock_cls.return_value.messages.create.return_value = mock_response

        with patch("builtins.input", return_value="a"):
            import coordinator
            coordinator._circuit_breaker.reset()
            state = coordinator.run_pipeline("BATCH-001")

        assert state.halted is False
        assert state.completed is True
        assert state.reporting.report_generated is True

    def test_run_pipeline_not_found(self):
        """run_pipeline with a non-existent batch returns halted state."""
        import coordinator
        coordinator._circuit_breaker.reset()
        state = coordinator.run_pipeline("NONEXISTENT")
        assert state.halted is True
        assert "not found" in state.halt_reason.lower()
