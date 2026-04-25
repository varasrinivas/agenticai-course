"""
Pipeline Coordinator — UCC Data Engineering Multi-Agent Pipeline (Solution)

Fully implemented orchestrator that runs 4 agents in sequence with
circuit breaker checks and structured logging.
"""

import json
import uuid
from datetime import datetime
from typing import Any

from agents import PipelineState
from agents.agent1 import IngestionAgent
from agents.agent2 import TransformationAgent
from agents.agent3 import QualityAgent
from agents.agent4 import ReportingAgent
from quality_gate import CircuitBreaker
from mock_data import FILING_BATCHES


# Module-level circuit breaker (persists across pipeline runs in a batch)
_circuit_breaker = CircuitBreaker(
    name="parse_errors",
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


def run_pipeline(batch_id: str) -> PipelineState:
    """
    Run the full 4-agent pipeline for a single UCC filing batch.
    """
    batch = FILING_BATCHES.get(batch_id)
    if not batch:
        print(f"[ERROR] Batch {batch_id} not found.")
        return PipelineState(halted=True, halt_reason=f"Batch {batch_id} not found")

    pipeline_id = f"PL-{uuid.uuid4().hex[:8].upper()}"
    state = PipelineState(
        pipeline_id=pipeline_id,
        started_at=datetime.now().isoformat(),
        raw_batch=batch,
    )

    print(f"\n{'#'*70}")
    print(f"# STARTING PIPELINE {pipeline_id}")
    print(f"# Batch: {batch_id} -- {batch.get('source', 'Unknown')}")
    print(f"# Format: {batch.get('format', 'N/A')} | Filings: {batch.get('filing_count', 0)}")
    print(f"{'#'*70}")

    ingestion_agent = IngestionAgent()
    transformation_agent = TransformationAgent()
    quality_agent = QualityAgent()
    reporting_agent = ReportingAgent()

    # ---------------------------------------------------------------
    # Agent 1: Ingestion
    # ---------------------------------------------------------------
    if _circuit_breaker.is_tripped():
        state.halted = True
        state.halt_reason = "Circuit breaker is OPEN -- too many parse failures."
        log_transition(pipeline_id, "START", "HALTED", state)
        return state

    state.current_agent = "IngestionAgent"
    log_transition(pipeline_id, "START", "IngestionAgent", state)
    state = ingestion_agent.run(state)

    # Determine success/failure for circuit breaker
    ingestion_failed = (
        state.ingestion.format_detected not in ("csv", "json", "xml")
        or state.ingestion.parse_error_count > 0
    )

    if ingestion_failed:
        _circuit_breaker.record_failure()
        if _circuit_breaker.is_tripped():
            state.halted = True
            state.halt_reason = "Circuit breaker tripped after ingestion failure."
            log_transition(pipeline_id, "IngestionAgent", "HALTED", state)
            return state
    else:
        _circuit_breaker.record_success()

    if state.halted:
        return state

    # If format unsupported, halt gracefully
    if state.ingestion.format_detected not in ("csv", "json", "xml"):
        state.halted = True
        state.halt_reason = f"Unsupported format: {state.ingestion.format_detected}"
        log_transition(pipeline_id, "IngestionAgent", "HALTED", state)
        return state

    # ---------------------------------------------------------------
    # Agent 2: Transformation
    # ---------------------------------------------------------------
    state.current_agent = "TransformationAgent"
    log_transition(pipeline_id, "IngestionAgent", "TransformationAgent", state)
    state = transformation_agent.run(state)

    if state.halted:
        return state

    # ---------------------------------------------------------------
    # Agent 3: Quality (with HITL gate)
    # ---------------------------------------------------------------
    state.current_agent = "QualityAgent"
    log_transition(pipeline_id, "TransformationAgent", "QualityAgent", state)
    state = quality_agent.run(state)

    if state.halted:
        return state

    # ---------------------------------------------------------------
    # Agent 4: Reporting
    # ---------------------------------------------------------------
    state.current_agent = "ReportingAgent"
    log_transition(pipeline_id, "QualityAgent", "ReportingAgent", state)
    state = reporting_agent.run(state)

    state.completed = True
    log_transition(pipeline_id, "ReportingAgent", "COMPLETED", state)

    # Print final summary
    print(f"\n{'*'*70}")
    print(f"PIPELINE {pipeline_id} COMPLETE")
    print(f"  Batch: {batch_id}")
    print(f"  Filings processed: {state.ingestion.filing_count}")
    print(f"  Quality score: {state.quality.quality_score}")
    print(f"  Entities profiled: {len(state.reporting.risk_profiles)}")
    print(f"  PII redactions: {state.reporting.redaction_count}")
    print(f"  Report generated: {state.reporting.report_generated}")
    print(f"{'*'*70}")

    return state


def run_batch(batch_ids: list[str]) -> list[PipelineState]:
    """Run the pipeline for a batch of filing batches (demonstrates circuit breaker)."""
    results = []
    for batch_id in batch_ids:
        state = run_pipeline(batch_id)
        results.append(state)
        if state.halted:
            print(f"\n[BATCH] Pipeline halted for {batch_id}: {state.halt_reason}")
    return results


def main():
    # --- Test 1: Happy path ---
    print("\n" + "=" * 70)
    print("TEST 1: Happy Path (BATCH-001 -- CA CSV, 5 filings, entity resolution)")
    print("=" * 70)
    _circuit_breaker.reset()
    state = run_pipeline("BATCH-001")
    print(f"\nResult: completed={state.completed}, quality={state.quality.quality_score}")
    print(f"Entities: {[p['canonical_name'] for p in state.reporting.risk_profiles]}")

    # --- Test 2: HITL trigger (malformed records) ---
    print("\n" + "=" * 70)
    print("TEST 2: HITL Trigger (BATCH-004 -- FL CSV, malformed records)")
    print("=" * 70)
    _circuit_breaker.reset()
    state = run_pipeline("BATCH-004")
    print(f"\nResult: completed={state.completed}, quality={state.quality.quality_score}")
    print(f"Halted: {state.halted}")
    if state.halted:
        print(f"Halt reason: {state.halt_reason}")

    # --- Test 3: Circuit breaker ---
    print("\n" + "=" * 70)
    print("TEST 3: Circuit Breaker (batch with failing records)")
    print("=" * 70)
    _circuit_breaker.reset()
    failing_batch = [
        "BATCH-009",  # Unknown xlsx format -- parse failure
        "BATCH-005",  # Duplicate filing numbers -- parse error
        "BATCH-009",  # Unknown xlsx format again -- should trip breaker
        "BATCH-001",  # Good batch -- may be blocked if breaker tripped
    ]
    results = run_batch(failing_batch)
    print("\nBatch Results:")
    for r in results:
        bid = r.raw_batch.get("batch_id", "?")
        status = "HALTED" if r.halted else ("COMPLETE" if r.completed else "INCOMPLETE")
        print(f"  {bid}: {status}")
    print(f"\nCircuit breaker status: {_circuit_breaker.get_status()}")


if __name__ == "__main__":
    main()
