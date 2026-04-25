"""
Pipeline Coordinator — UCC Data Engineering Multi-Agent Pipeline

The coordinator orchestrates 4 agents in sequence:
  Ingestion Agent -> Transformation Agent -> Quality Agent -> Reporting Agent

It manages:
- Pipeline state initialization and passing between agents
- Circuit breaker checks before each agent transition
- Structured logging at every stage
- HITL pause/resume handling from the Quality Agent

YOUR TASK: Complete the TODO sections to wire the full pipeline.
"""

import json
import uuid
from datetime import datetime
from typing import Any

from agents import PipelineState, IngestionResult, TransformationResult, QualityResult, ReportingResult
from agents.agent1 import IngestionAgent
from agents.agent2 import TransformationAgent
from agents.agent3 import QualityAgent
from agents.agent4 import ReportingAgent
from quality_gate import CircuitBreaker
from mock_data import FILING_BATCHES


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


def run_pipeline(batch_id: str) -> PipelineState:
    """
    Run the full 4-agent pipeline for a single UCC filing batch.

    Args:
        batch_id: The batch ID to process.

    Returns:
        The final PipelineState after all agents have run.
    """
    # --- Look up the batch ---
    batch = FILING_BATCHES.get(batch_id)
    if not batch:
        print(f"[ERROR] Batch {batch_id} not found.")
        state = PipelineState(halted=True, halt_reason=f"Batch {batch_id} not found")
        return state

    # --- Initialize pipeline state ---
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

    # --- Initialize agents ---
    # TODO: Create instances of all 4 agents
    # ingestion_agent = IngestionAgent()
    # transformation_agent = TransformationAgent()
    # quality_agent = QualityAgent()
    # reporting_agent = ReportingAgent()

    # --- Initialize circuit breaker ---
    # TODO: Create a CircuitBreaker instance
    # circuit_breaker = CircuitBreaker(
    #     name="parse_errors",
    #     failure_threshold=0.10,  # Trip at > 10% failure rate
    #     window_size=20,
    # )

    # --- Agent 1: Ingestion ---
    # TODO: Implement Agent 1 execution
    # 1. Check circuit breaker — if tripped, halt pipeline
    # 2. Set state.current_agent = "IngestionAgent"
    # 3. Run ingestion_agent.run(state)
    # 4. Record success/failure in circuit breaker based on parse errors
    #    (failure = unsupported format OR parse_error_count > 0)
    # 5. Log transition
    # 6. If format unsupported or parse errors, decide whether to halt

    # --- Agent 2: Transformation ---
    # TODO: Implement Agent 2 execution
    # 1. Check circuit breaker
    # 2. Set state.current_agent = "TransformationAgent"
    # 3. Run transformation_agent.run(state)
    # 4. Log transition

    # --- Agent 3: Quality (with HITL gate) ---
    # TODO: Implement Agent 3 execution
    # 1. Set state.current_agent = "QualityAgent"
    # 2. Run quality_agent.run(state)
    # 3. Handle HITL result if triggered (quality_score < 80% or low_confidence > 0)
    # 4. If HITL reviewer rejects, halt pipeline
    # 5. Log transition

    # --- Agent 4: Reporting ---
    # TODO: Implement Agent 4 execution
    # 1. Set state.current_agent = "ReportingAgent"
    # 2. Run reporting_agent.run(state)
    # 3. Mark state.completed = True
    # 4. Log transition

    return state


def run_batch(batch_ids: list[str]) -> list[PipelineState]:
    """
    Run the pipeline for a batch of filing batches.

    This demonstrates the circuit breaker across multiple batches.
    """
    results = []
    for batch_id in batch_ids:
        state = run_pipeline(batch_id)
        results.append(state)

        if state.halted:
            print(f"\n[BATCH] Pipeline halted for {batch_id}: {state.halt_reason}")

    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    # --- Test 1: Happy path ---
    print("\n" + "=" * 70)
    print("TEST 1: Happy Path (BATCH-001 — CA CSV, 5 filings, entity resolution)")
    print("=" * 70)
    state = run_pipeline("BATCH-001")
    print(f"\nCompleted: {state.completed}")
    print(f"Quality score: {state.quality.quality_score}")
    print(f"Report generated: {state.reporting.report_generated}")

    # --- Test 2: HITL trigger ---
    print("\n" + "=" * 70)
    print("TEST 2: HITL Trigger (BATCH-004 — FL CSV, malformed records)")
    print("=" * 70)
    state = run_pipeline("BATCH-004")
    print(f"\nCompleted: {state.completed}")
    print(f"Quality score: {state.quality.quality_score}")
    print(f"Halted: {state.halted}")

    # --- Test 3: Circuit breaker ---
    print("\n" + "=" * 70)
    print("TEST 3: Circuit Breaker (batch of failing records)")
    print("=" * 70)
    failing_batch = [
        "BATCH-009",  # Unknown xlsx format — parse failure
        "BATCH-005",  # Duplicate filing numbers
        "BATCH-009",  # Unknown xlsx format again — should trip breaker
        "BATCH-001",  # Good batch — may be blocked if breaker tripped
    ]
    results = run_batch(failing_batch)
    for r in results:
        batch = r.raw_batch.get("batch_id", "?")
        status = "HALTED" if r.halted else ("COMPLETE" if r.completed else "INCOMPLETE")
        print(f"  {batch}: {status}")


if __name__ == "__main__":
    main()
