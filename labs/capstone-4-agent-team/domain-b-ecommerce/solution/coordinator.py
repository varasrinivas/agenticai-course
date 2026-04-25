"""
Pipeline Coordinator — B2B Ecommerce Order Pipeline (Solution)
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

_circuit_breaker = CircuitBreaker(name="sla_violations", max_consecutive_failures=3)


def log_transition(pid, from_a, to_a, state):
    print(f"\n{'='*60}")
    print(f"[{datetime.now().isoformat()}] {pid}: {from_a} -> {to_a} (halted={state.halted})")
    print(f"{'='*60}")


def run_pipeline(order_id):
    order = ORDERS.get(order_id)
    if not order:
        return PipelineState(halted=True, halt_reason=f"Order {order_id} not found")

    pid = f"PL-{uuid.uuid4().hex[:8].upper()}"
    state = PipelineState(pipeline_id=pid, started_at=datetime.now().isoformat(), raw_order=order)
    print(f"\n{'#'*60}\n# Pipeline {pid} -- {order_id} ({order.get('customer_name')})\n{'#'*60}")

    if _circuit_breaker.is_tripped():
        state.halted = True
        state.halt_reason = "Circuit breaker OPEN"
        return state

    # Agent 1
    state.current_agent = "OrderIntakeAgent"
    log_transition(pid, "START", "OrderIntakeAgent", state)
    state = OrderIntakeAgent().run(state)
    if not state.intake.validation_passed:
        _circuit_breaker.record_failure()
    else:
        _circuit_breaker.record_success()
    if state.halted:
        return state

    # Agent 2
    state.current_agent = "FulfillmentPlanningAgent"
    log_transition(pid, "OrderIntakeAgent", "FulfillmentPlanningAgent", state)
    state = FulfillmentPlanningAgent().run(state)
    if state.halted:
        return state

    # Agent 3
    state.current_agent = "ExceptionMonitorAgent"
    log_transition(pid, "FulfillmentPlanningAgent", "ExceptionMonitorAgent", state)
    state = ExceptionMonitorAgent().run(state)
    if state.exception.sla_status == "violated":
        _circuit_breaker.record_failure()
    if _circuit_breaker.is_tripped():
        state.halted = True
        state.halt_reason = "Circuit breaker tripped: consecutive SLA violations"
        return state
    if state.halted:
        return state

    # Agent 4
    state.current_agent = "CommunicationAgent"
    log_transition(pid, "ExceptionMonitorAgent", "CommunicationAgent", state)
    state = CommunicationAgent().run(state)
    state.completed = True
    log_transition(pid, "CommunicationAgent", "COMPLETED", state)

    print(f"\n{'*'*60}\nPipeline {pid} COMPLETE\n  Order: {order_id}\n  SLA: {state.exception.sla_status}\n  Carrier: {state.fulfillment.selected_carrier}\n{'*'*60}")
    return state


def main():
    _circuit_breaker.reset()
    print("=== TEST 1: Happy Path ===")
    run_pipeline("PO-2024-5001")

    print("\n=== TEST 2: Split Shipment (HITL) ===")
    run_pipeline("PO-2024-5007")

    print("\n=== TEST 3: Invalid SKU ===")
    run_pipeline("PO-2024-5006")


if __name__ == "__main__":
    main()
