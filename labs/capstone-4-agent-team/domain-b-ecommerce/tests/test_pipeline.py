"""
Tests for the B2B Ecommerce Order Pipeline — Domain B.

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
    OrderIntakeResult,
    FulfillmentResult,
    ExceptionResult,
    CommunicationResult,
)
from agents.agent1 import OrderIntakeAgent
from agents.agent2 import FulfillmentPlanningAgent
from agents.agent3 import ExceptionMonitorAgent
from agents.agent4 import CommunicationAgent
from quality_gate import CircuitBreaker
from mock_data import ORDERS, INVENTORY, CONTRACT_PRICING, SLA_RULES, CARRIERS


# ---------------------------------------------------------------------------
# PipelineState initialization
# ---------------------------------------------------------------------------
class TestPipelineState:
    def test_default_state(self):
        state = PipelineState()
        assert state.pipeline_id == ""
        assert state.halted is False
        assert state.completed is False
        assert isinstance(state.intake, OrderIntakeResult)
        assert isinstance(state.fulfillment, FulfillmentResult)
        assert isinstance(state.exception, ExceptionResult)
        assert isinstance(state.communication, CommunicationResult)

    def test_state_with_values(self):
        state = PipelineState(
            pipeline_id="PL-TEST",
            started_at="2024-11-20T10:00:00",
        )
        assert state.pipeline_id == "PL-TEST"

    def test_agent_trace_starts_empty(self):
        state = PipelineState()
        assert state.agent_trace == []

    def test_raw_order_starts_empty(self):
        state = PipelineState()
        assert state.raw_order == {}


# ---------------------------------------------------------------------------
# Agent instantiation
# ---------------------------------------------------------------------------
class TestAgentInstantiation:
    def test_order_intake_agent(self):
        agent = OrderIntakeAgent()
        assert agent.name == "OrderIntakeAgent"
        assert len(agent.tool_schemas) > 0

    def test_fulfillment_planning_agent(self):
        agent = FulfillmentPlanningAgent()
        assert agent.name == "FulfillmentPlanningAgent"
        assert len(agent.tool_schemas) > 0

    def test_exception_monitor_agent(self):
        agent = ExceptionMonitorAgent()
        assert agent.name == "ExceptionMonitorAgent"
        assert len(agent.tool_schemas) > 0

    def test_communication_agent(self):
        agent = CommunicationAgent()
        assert agent.name == "CommunicationAgent"
        assert len(agent.tool_schemas) > 0


# ---------------------------------------------------------------------------
# Mock data is well-formed
# ---------------------------------------------------------------------------
class TestMockData:
    def test_orders_not_empty(self):
        assert len(ORDERS) > 0

    def test_orders_has_expected_keys(self):
        assert "PO-2024-5001" in ORDERS  # happy path
        assert "PO-2024-5006" in ORDERS  # invalid SKU
        assert "PO-2024-5007" in ORDERS  # split shipment

    def test_order_structure(self):
        order = ORDERS["PO-2024-5001"]
        required_fields = [
            "order_id", "customer_id", "customer_name", "items",
            "shipping_address", "requested_delivery", "sla_tier",
            "po_status", "submitted_date",
        ]
        for field in required_fields:
            assert field in order, f"Missing field: {field}"

    def test_order_items_have_required_fields(self):
        order = ORDERS["PO-2024-5001"]
        for item in order["items"]:
            assert "sku" in item
            assert "qty" in item
            assert "unit_price" in item

    def test_inventory_has_warehouses(self):
        assert len(INVENTORY) > 0
        assert "WH-EAST" in INVENTORY
        assert "WH-CENTRAL" in INVENTORY
        assert "WH-WEST" in INVENTORY

    def test_inventory_warehouse_has_stock(self):
        wh = INVENTORY["WH-EAST"]
        assert "stock" in wh
        assert "WDG-4420" in wh["stock"]
        assert wh["stock"]["WDG-4420"] > 0

    def test_contract_pricing_has_entries(self):
        assert len(CONTRACT_PRICING) > 0
        assert "CUST-100" in CONTRACT_PRICING

    def test_sla_rules_has_tiers(self):
        assert "economy" in SLA_RULES
        assert "standard" in SLA_RULES
        assert "expedited" in SLA_RULES

    def test_carriers_has_entries(self):
        assert len(CARRIERS) > 0


# ---------------------------------------------------------------------------
# CircuitBreaker integration
# ---------------------------------------------------------------------------
class TestCircuitBreakerIntegration:
    def test_breaker_tracks_consecutive_failures(self):
        cb = CircuitBreaker(name="test", max_consecutive_failures=3)
        cb.record_failure()
        cb.record_failure()
        status = cb.get_status()
        assert status["consecutive_failures"] == 2

    def test_breaker_trips_after_threshold(self):
        cb = CircuitBreaker(name="test", max_consecutive_failures=3)
        for _ in range(4):
            cb.record_failure()
        assert cb.is_tripped() is True

    def test_success_resets_consecutive_count(self):
        cb = CircuitBreaker(name="test", max_consecutive_failures=3)
        cb.record_failure()
        cb.record_failure()
        cb.record_success()
        status = cb.get_status()
        assert status["consecutive_failures"] == 0


# ---------------------------------------------------------------------------
# Pipeline end-to-end (mocking Anthropic API)
# ---------------------------------------------------------------------------
class TestPipelineRun:
    @patch("agents.agent1.anthropic.Anthropic")
    @patch("agents.agent2.anthropic.Anthropic")
    @patch("agents.agent3.anthropic.Anthropic")
    @patch("agents.agent4.anthropic.Anthropic")
    def test_run_pipeline_happy_path(self, mock_a4, mock_a3, mock_a2, mock_a1):
        """Mock all Anthropic calls and run the pipeline for PO-2024-5001."""
        mock_response = MagicMock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [MagicMock(type="text", text="Done.")]

        for mock_cls in [mock_a1, mock_a2, mock_a3, mock_a4]:
            mock_cls.return_value.messages.create.return_value = mock_response

        with patch("builtins.input", return_value="a"):
            import coordinator
            coordinator._circuit_breaker.reset()
            state = coordinator.run_pipeline("PO-2024-5001")

        assert state.halted is False
        assert state.completed is True

    def test_run_pipeline_not_found(self):
        """run_pipeline with a non-existent order returns halted state."""
        import coordinator
        coordinator._circuit_breaker.reset()
        state = coordinator.run_pipeline("NONEXISTENT")
        assert state.halted is True
        assert "not found" in state.halt_reason.lower()
