"""
M14 Lab -- Multi-Agent Systems: Coordinator (Starter)
=====================================================
Orchestrates the 4-agent pipeline:
  Researcher -> Analyst -> Writer -> Reviewer

Each agent gets ISOLATED context (fresh messages each time).
The coordinator explicitly passes data between agents.

Usage:
    python coordinator.py "Acme Corporation"
    python coordinator.py  # defaults to "Acme Corporation"
"""

import json
import sys
import os
import time
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from researcher import run_researcher
from analyst import run_analyst
from writer import run_writer
from reviewer import run_reviewer


# =============================================================================
# OBSERVATION HELPERS (complete — do not modify)
# =============================================================================

def observe(label: str, message: str) -> None:
    """Log a coordinator-level event."""
    print(f"\n{'=' * 60}")
    print(f"[{label}] {message}")
    print(f"{'=' * 60}")


def observe_handoff(from_agent: str, to_agent: str, data_size: int) -> None:
    """Log a data handoff between agents."""
    print(f"\n{'─' * 60}")
    print(f"[HANDOFF] {from_agent} -> {to_agent} ({data_size:,} chars)")
    print(f"{'─' * 60}")


def observe_phase(phase_num: int, total: int, description: str) -> None:
    """Log a pipeline phase."""
    print(f"\n{'*' * 60}")
    print(f"[PHASE {phase_num}/{total}] {description}")
    print(f"{'*' * 60}")


# =============================================================================
# COORDINATOR — YOUR CODE HERE
# =============================================================================

def run_pipeline(entity_name: str) -> str:
    """
    Orchestrate the 4-agent content pipeline.

    Pipeline:
      1. Researcher: find all UCC filings for the entity
      2. Analyst: analyze patterns and calculate risk
      3. Writer: generate formatted risk report
      4. Reviewer: verify accuracy against source data

    Each agent gets ISOLATED context — the coordinator explicitly
    passes the output of one agent as input to the next.

    Args:
        entity_name: The company/entity to research

    Returns:
        Final reviewed report string
    """
    start_time = time.time()
    observe("COORDINATOR", f"Starting pipeline for: {entity_name}")

    # ------------------------------------------------------------------
    # TODO Step 1: Run the Researcher
    #   - Call run_researcher(entity_name)
    #   - Store the result as research_data
    #   - Log the handoff: observe_handoff("Researcher", "Analyst", len(research_data))
    #   - Check if the researcher found anything:
    #       parsed = json.loads(research_data)
    #       if parsed.get("total_found", 0) == 0:
    #           return "No filings found for {entity_name}. Pipeline complete."
    # ------------------------------------------------------------------
    observe_phase(1, 4, "Research — Gathering UCC filings")
    research_data = None  # Replace with your code

    # ------------------------------------------------------------------
    # TODO Step 2: Run the Analyst
    #   - Call run_analyst(research_data)
    #   - Store the result as analysis
    #   - Log the handoff: observe_handoff("Analyst", "Writer", len(analysis))
    # ------------------------------------------------------------------
    observe_phase(2, 4, "Analysis — Identifying patterns and risk")
    analysis = None  # Replace with your code

    # ------------------------------------------------------------------
    # TODO Step 3: Run the Writer
    #   - Call run_writer(research_data, analysis)
    #   - Store the result as report
    #   - Log the handoff: observe_handoff("Writer", "Reviewer", len(report))
    # ------------------------------------------------------------------
    observe_phase(3, 4, "Writing — Generating risk report")
    report = None  # Replace with your code

    # ------------------------------------------------------------------
    # TODO Step 4: Run the Reviewer
    #   - Call run_reviewer(report, research_data)
    #   - Store the result as review
    # ------------------------------------------------------------------
    observe_phase(4, 4, "Review — Verifying accuracy")
    review = None  # Replace with your code

    # ------------------------------------------------------------------
    # TODO Step 5: Assemble final output
    #   Combine the report and review verdict into a single output string.
    # ------------------------------------------------------------------
    elapsed = time.time() - start_time
    observe("COORDINATOR", f"Pipeline complete in {elapsed:.1f}s")

    # Placeholder output
    final_output = f"""=== PIPELINE RESULT ===
Entity: {entity_name}
Status: TODO — implement run_pipeline()

Research: {'found data' if research_data else 'not run'}
Analysis: {'complete' if analysis else 'not run'}
Report: {'generated' if report else 'not run'}
Review: {'complete' if review else 'not run'}

Elapsed: {elapsed:.1f}s
"""
    return final_output


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    entity = sys.argv[1] if len(sys.argv) > 1 else "Acme Corporation"

    print("=" * 60)
    print("M14 Lab — Multi-Agent Content Pipeline")
    print("=" * 60)
    print(f"Entity: {entity}")
    print("=" * 60)

    result = run_pipeline(entity)

    print("\n" + "=" * 60)
    print("FINAL REPORT")
    print("=" * 60)
    print(result)
