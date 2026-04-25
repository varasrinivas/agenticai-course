"""
Pipeline Coordinator — Healthcare Pre-Auth Multi-Agent Pipeline

The coordinator orchestrates 4 agents in sequence:
  Intake Agent -> Clinical Criteria Agent -> Decision Agent -> Communication Agent

It manages:
- Pipeline state initialization and passing between agents
- Circuit breaker checks before each agent transition
- Structured logging at every stage
- HITL pause/resume handling from the Decision Agent

YOUR TASK: Complete the TODO sections to wire the full pipeline.
"""

import json
import uuid
from datetime import datetime
from typing import Any

from agents import PipelineState, IntakeResult, CriteriaResult, DecisionResult, CommunicationResult
from agents.agent1 import IntakeAgent
from agents.agent2 import ClinicalCriteriaAgent
from agents.agent3 import DecisionAgent
from agents.agent4 import CommunicationAgent
from quality_gate import CircuitBreaker
from mock_data import PREAUTH_REQUESTS


def log_transition(pipeline_id: str, from_agent: str, to_agent: str, state: PipelineState):
    """Log a structured agent transition."""
    timestamp = datetime.now().isoformat()
    print(f"\n{'='*70}")
    print(f"[{timestamp}] PIPELINE {pipeline_id}")
    print(f"  Transition: {from_agent} -> {to_agent}")
    print(f"  State halted: {state.halted}")
    if state.halted:
        print(f"  Halt reason: {state.halt_reason}")
    print(f"{'='*70}")


def run_pipeline(request_id: str) -> PipelineState:
    """
    Run the full 4-agent pipeline for a single pre-authorization request.

    Args:
        request_id: The pre-authorization request ID to process.

    Returns:
        The final PipelineState after all agents have run.
    """
    # --- Look up the request ---
    request = PREAUTH_REQUESTS.get(request_id)
    if not request:
        print(f"[ERROR] Request {request_id} not found.")
        state = PipelineState(halted=True, halt_reason=f"Request {request_id} not found")
        return state

    # --- Initialize pipeline state ---
    pipeline_id = f"PL-{uuid.uuid4().hex[:8].upper()}"
    state = PipelineState(
        pipeline_id=pipeline_id,
        started_at=datetime.now().isoformat(),
        raw_request=request,
    )

    print(f"\n{'#'*70}")
    print(f"# STARTING PIPELINE {pipeline_id}")
    print(f"# Request: {request_id} — {request.get('patient_name', 'Unknown')}")
    print(f"# CPT: {request.get('cpt_code', 'N/A')} | Dx: {request.get('diagnosis_codes', [])}")
    print(f"{'#'*70}")

    # --- Initialize agents ---
    # TODO: Create instances of all 4 agents
    # intake_agent = IntakeAgent()
    # criteria_agent = ClinicalCriteriaAgent()
    # decision_agent = DecisionAgent()
    # communication_agent = CommunicationAgent()

    # --- Initialize circuit breaker ---
    # TODO: Create a CircuitBreaker instance
    # circuit_breaker = CircuitBreaker(
    #     name="intake_validation",
    #     failure_threshold=0.10,  # Trip at > 10% failure rate
    #     window_size=20,
    # )

    # --- Agent 1: Intake ---
    # TODO: Implement Agent 1 execution
    # 1. Check circuit breaker — if tripped, halt pipeline
    # 2. Set state.current_agent = "IntakeAgent"
    # 3. Run intake_agent.run(state)
    # 4. Record success/failure in circuit breaker
    # 5. Log transition
    # 6. If intake validation failed, decide whether to continue or halt

    # --- Agent 2: Clinical Criteria ---
    # TODO: Implement Agent 2 execution
    # 1. Check circuit breaker
    # 2. Set state.current_agent = "ClinicalCriteriaAgent"
    # 3. Run criteria_agent.run(state)
    # 4. Log transition

    # --- Agent 3: Decision ---
    # TODO: Implement Agent 3 execution
    # 1. Set state.current_agent = "DecisionAgent"
    # 2. Run decision_agent.run(state)
    # 3. Handle HITL result if triggered
    # 4. Log transition

    # --- Agent 4: Communication ---
    # TODO: Implement Agent 4 execution
    # 1. Set state.current_agent = "CommunicationAgent"
    # 2. Run communication_agent.run(state)
    # 3. Mark state.completed = True
    # 4. Log transition

    return state


def run_batch(request_ids: list[str]) -> list[PipelineState]:
    """
    Run the pipeline for a batch of requests.

    This demonstrates the circuit breaker across multiple requests.
    """
    results = []
    for request_id in request_ids:
        state = run_pipeline(request_id)
        results.append(state)

        if state.halted:
            print(f"\n[BATCH] Pipeline halted for {request_id}: {state.halt_reason}")

    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    # --- Test 1: Happy path ---
    print("\n" + "=" * 70)
    print("TEST 1: Happy Path (PA-2024-001 — should be APPROVED)")
    print("=" * 70)
    state = run_pipeline("PA-2024-001")
    print(f"\nFinal determination: {state.decision.determination}")
    print(f"Completed: {state.completed}")

    # --- Test 2: HITL trigger ---
    print("\n" + "=" * 70)
    print("TEST 2: HITL Trigger (PA-2024-012 — borderline WOMAC score)")
    print("=" * 70)
    state = run_pipeline("PA-2024-012")
    print(f"\nFinal determination: {state.decision.determination}")
    print(f"HITL triggered: {state.decision.hitl_triggered}")

    # --- Test 3: Circuit breaker ---
    print("\n" + "=" * 70)
    print("TEST 3: Circuit Breaker (batch with failing records)")
    print("=" * 70)
    failing_batch = [
        "PA-2024-009",  # Invalid CPT
        "PA-2024-010",  # Missing diagnosis
        "PA-2024-009",  # Invalid CPT again
        "PA-2024-001",  # Good request — should still work if breaker not tripped
    ]
    results = run_batch(failing_batch)
    for r in results:
        status = "HALTED" if r.halted else r.decision.determination or "INCOMPLETE"
        print(f"  {r.raw_request.get('request_id', '?')}: {status}")


if __name__ == "__main__":
    main()
