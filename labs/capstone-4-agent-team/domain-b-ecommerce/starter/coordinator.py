"""
Pipeline Coordinator — B2B Ecommerce Order Pipeline

Orchestrates: Order Intake -> Fulfillment Planning -> Exception Monitor -> Communication
Circuit breaker: trips on > 3 consecutive SLA violations.
HITL gate: Fulfillment agent when split-shipment needed.

YOUR TASK: Complete the TODO sections to wire the full pipeline.
"""

import json
import uuid
from datetime import datetime

from agents import PipelineState
from agents.agent1 import OrderIntakeAgent
from agents.agent2 import FulfillmentPlanningAgent
from agents.agent3 import ExceptionMonitorAgent
from agents.agent4 import CommunicationAgent
from quality_gate import CircuitBreaker
from mock_data import ORDERS


def log_transition(pipeline_id: str, from_agent: str, to_agent: str, state: PipelineState):
    timestamp = datetime.now().isoformat()
    print(f"\n{'='*70}")
    print(f"[{timestamp}] PIPELINE {pipeline_id}")
    print(f"  Transition: {from_agent} -> {to_agent}")
    print(f"  Halted: {state.halted}")
    print(f"{'='*70}")


def run_pipeline(order_id: str) -> PipelineState:
    """Run the full 4-agent pipeline for a purchase order."""
    order = ORDERS.get(order_id)
    if not order:
        return PipelineState(halted=True, halt_reason=f"Order {order_id} not found")

    pipeline_id = f"PL-{uuid.uuid4().hex[:8].upper()}"
    state = PipelineState(
        pipeline_id=pipeline_id,
        started_at=datetime.now().isoformat(),
        raw_order=order,
    )

    print(f"\n{'#'*70}")
    print(f"# PIPELINE {pipeline_id} — Order {order_id}")
    print(f"# Customer: {order.get('customer_name')}")
    print(f"{'#'*70}")

    # TODO: Initialize agents and circuit breaker
    # TODO: Run Agent 1 (Order Intake)
    # TODO: Run Agent 2 (Fulfillment Planning) — with HITL for split shipments
    # TODO: Run Agent 3 (Exception Monitor) — update circuit breaker
    # TODO: Run Agent 4 (Communication)
    # TODO: Mark state.completed = True

    return state


def main():
    print("=== TEST 1: Happy Path ===")
    state = run_pipeline("PO-2024-5001")
    print(f"Result: {state.completed}")

    print("\n=== TEST 2: Split Shipment (HITL) ===")
    state = run_pipeline("PO-2024-5007")
    print(f"Split shipment: {state.fulfillment.split_shipment_needed}")

    print("\n=== TEST 3: Invalid SKU ===")
    state = run_pipeline("PO-2024-5006")
    print(f"Validation errors: {state.intake.validation_errors}")


if __name__ == "__main__":
    main()
