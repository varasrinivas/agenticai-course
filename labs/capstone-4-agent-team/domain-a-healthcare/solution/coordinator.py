"""
Pipeline Coordinator — Healthcare Pre-Auth Multi-Agent Pipeline (Solution)

Fully implemented orchestrator that runs 4 agents in sequence with
circuit breaker checks and structured logging.
"""

import json
import uuid
from datetime import datetime
from typing import Any

from agents import PipelineState
from agents.agent1 import IntakeAgent
from agents.agent2 import ClinicalCriteriaAgent
from agents.agent3 import DecisionAgent
from agents.agent4 import CommunicationAgent
from quality_gate import CircuitBreaker
from mock_data import PREAUTH_REQUESTS


# Module-level circuit breaker (persists across pipeline runs in a batch)
_circuit_breaker = CircuitBreaker(
    name="intake_validation",
    failure_threshold=0.10,
    window_size=20,
)


def log_transition(pipeline_id: str, from_agent: str, to_agent: str, state: PipelineState):
    """Log a structured agent transition."""
    timestamp = datetime.now().isoformat()
    print(f"\n{'='*70}")
    print(f"[{timestamp}] PIPELINE {pipeline_id}")
    print(f"  Transition: {from_agent} -> {to_agent}")
    print(f"  State halted: {state.halted}")
    if state.halted:
        print(f"  Halt reason: {state.halt_reason}")
    print(f"  Circuit breaker: {_circuit_breaker.get_status()}")
    print(f"{'='*70}")


def run_pipeline(request_id: str) -> PipelineState:
    """
    Run the full 4-agent pipeline for a single pre-authorization request.
    """
    request = PREAUTH_REQUESTS.get(request_id)
    if not request:
        print(f"[ERROR] Request {request_id} not found.")
        return PipelineState(halted=True, halt_reason=f"Request {request_id} not found")

    pipeline_id = f"PL-{uuid.uuid4().hex[:8].upper()}"
    state = PipelineState(
        pipeline_id=pipeline_id,
        started_at=datetime.now().isoformat(),
        raw_request=request,
    )

    print(f"\n{'#'*70}")
    print(f"# STARTING PIPELINE {pipeline_id}")
    print(f"# Request: {request_id} -- {request.get('patient_name', 'Unknown')}")
    print(f"# CPT: {request.get('cpt_code', 'N/A')} | Dx: {request.get('diagnosis_codes', [])}")
    print(f"{'#'*70}")

    intake_agent = IntakeAgent()
    criteria_agent = ClinicalCriteriaAgent()
    decision_agent = DecisionAgent()
    communication_agent = CommunicationAgent()

    # ---------------------------------------------------------------
    # Agent 1: Intake
    # ---------------------------------------------------------------
    if _circuit_breaker.is_tripped():
        state.halted = True
        state.halt_reason = "Circuit breaker is OPEN — too many intake validation failures."
        log_transition(pipeline_id, "START", "HALTED", state)
        return state

    state.current_agent = "IntakeAgent"
    log_transition(pipeline_id, "START", "IntakeAgent", state)
    state = intake_agent.run(state)

    if state.intake.validation_passed:
        _circuit_breaker.record_success()
    else:
        _circuit_breaker.record_failure()
        if _circuit_breaker.is_tripped():
            state.halted = True
            state.halt_reason = "Circuit breaker tripped after intake validation failure."
            log_transition(pipeline_id, "IntakeAgent", "HALTED", state)
            return state

    if not state.intake.validation_passed:
        print(f"  [WARN] Intake validation failed: {state.intake.validation_errors}")
        print(f"  [WARN] Continuing with available data for downstream evaluation.")

    if state.halted:
        return state

    # ---------------------------------------------------------------
    # Agent 2: Clinical Criteria
    # ---------------------------------------------------------------
    state.current_agent = "ClinicalCriteriaAgent"
    log_transition(pipeline_id, "IntakeAgent", "ClinicalCriteriaAgent", state)
    state = criteria_agent.run(state)

    if state.halted:
        return state

    # ---------------------------------------------------------------
    # Agent 3: Decision (with HITL gate)
    # ---------------------------------------------------------------
    state.current_agent = "DecisionAgent"
    log_transition(pipeline_id, "ClinicalCriteriaAgent", "DecisionAgent", state)
    state = decision_agent.run(state)

    if state.halted:
        return state

    # ---------------------------------------------------------------
    # Agent 4: Communication
    # ---------------------------------------------------------------
    state.current_agent = "CommunicationAgent"
    log_transition(pipeline_id, "DecisionAgent", "CommunicationAgent", state)
    state = communication_agent.run(state)

    state.completed = True
    log_transition(pipeline_id, "CommunicationAgent", "COMPLETED", state)

    # Print final summary
    print(f"\n{'*'*70}")
    print(f"PIPELINE {pipeline_id} COMPLETE")
    print(f"  Request: {request_id}")
    print(f"  Determination: {state.decision.determination}")
    print(f"  Confidence: {state.decision.confidence}%")
    print(f"  HITL Triggered: {state.decision.hitl_triggered}")
    print(f"  Letter Format: {state.communication.letter_format}")
    print(f"  Communication Logged: {state.communication.communication_logged}")
    print(f"{'*'*70}")

    return state


def run_batch(request_ids: list[str]) -> list[PipelineState]:
    """Run the pipeline for a batch of requests (demonstrates circuit breaker)."""
    results = []
    for request_id in request_ids:
        state = run_pipeline(request_id)
        results.append(state)
        if state.halted:
            print(f"\n[BATCH] Pipeline halted for {request_id}: {state.halt_reason}")
    return results


def main():
    # --- Test 1: Happy path ---
    print("\n" + "=" * 70)
    print("TEST 1: Happy Path (PA-2024-001 — should be APPROVED)")
    print("=" * 70)
    _circuit_breaker.reset()
    state = run_pipeline("PA-2024-001")
    print(f"\nResult: {state.decision.determination} (confidence: {state.decision.confidence}%)")

    # --- Test 2: HITL trigger (borderline score) ---
    print("\n" + "=" * 70)
    print("TEST 2: HITL Trigger (PA-2024-012 — borderline WOMAC score)")
    print("=" * 70)
    _circuit_breaker.reset()
    state = run_pipeline("PA-2024-012")
    print(f"\nResult: {state.decision.determination}")
    print(f"HITL triggered: {state.decision.hitl_triggered}")
    print(f"HITL decision: {state.decision.hitl_decision}")

    # --- Test 3: Circuit breaker ---
    print("\n" + "=" * 70)
    print("TEST 3: Circuit Breaker (batch with failing records)")
    print("=" * 70)
    _circuit_breaker.reset()
    failing_batch = [
        "PA-2024-009",  # Invalid CPT
        "PA-2024-010",  # Missing diagnosis
        "PA-2024-009",  # Invalid CPT again
        "PA-2024-001",  # Good request — may be blocked if breaker tripped
    ]
    results = run_batch(failing_batch)
    print("\nBatch Results:")
    for r in results:
        req_id = r.raw_request.get("request_id", "?")
        status = "HALTED" if r.halted else r.decision.determination or "INCOMPLETE"
        print(f"  {req_id}: {status}")
    print(f"\nCircuit breaker status: {_circuit_breaker.get_status()}")


if __name__ == "__main__":
    main()
