"""
M14 Lab -- Multi-Agent Systems: Coordinator (Solution)
======================================================
Orchestrates the 4-agent pipeline:
  Researcher -> Analyst -> Writer -> Reviewer

Each agent gets ISOLATED context (fresh messages each time).
The coordinator explicitly passes data between agents and
handles failures gracefully.

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

# Allow imports from both solution/ (this dir) and starter/ (for tools.py)
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "starter"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from researcher import run_researcher
from analyst import run_analyst
from writer import run_writer
from reviewer import run_reviewer


# =============================================================================
# OBSERVATION HELPERS
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
# COORDINATOR — SOLUTION
# =============================================================================

def run_pipeline(entity_name: str) -> str:
    """
    Orchestrate the 4-agent content pipeline.

    Pipeline:
      1. Researcher: find all UCC filings for the entity
      2. Analyst: analyze patterns and calculate risk
      3. Writer: generate formatted risk report
      4. Reviewer: verify accuracy against source data

    Each agent gets ISOLATED context. The coordinator explicitly
    passes the output of one agent as input to the next.

    Args:
        entity_name: The company/entity to research

    Returns:
        Final reviewed report string
    """
    start_time = time.time()
    observe("COORDINATOR", f"Starting pipeline for: {entity_name}")

    # ------------------------------------------------------------------
    # Phase 1: Research — gather raw filing data
    # ------------------------------------------------------------------
    observe_phase(1, 4, "Research — Gathering UCC filings")
    try:
        research_data = run_researcher(entity_name)
    except Exception as e:
        observe("ERROR", f"Researcher failed: {e}")
        return f"Pipeline failed at Research phase: {e}"

    observe_handoff("Researcher", "Analyst", len(research_data))

    # Check if the researcher found anything
    try:
        parsed_research = json.loads(research_data)
        filing_count = parsed_research.get("total_found", 0)
    except (json.JSONDecodeError, TypeError):
        # If the response isn't valid JSON, the researcher still returned
        # something useful (free-text findings). Continue the pipeline.
        filing_count = -1  # unknown, proceed anyway

    if filing_count == 0:
        observe("COORDINATOR", f"No filings found for '{entity_name}'. Skipping remaining phases.")
        return (
            f"No UCC filings found for '{entity_name}'.\n"
            f"The researcher searched all available states and found no matching records.\n"
            f"Pipeline complete (Research phase only)."
        )

    # ------------------------------------------------------------------
    # Phase 2: Analysis — identify patterns and risk
    # ------------------------------------------------------------------
    observe_phase(2, 4, "Analysis — Identifying patterns and risk")
    try:
        analysis = run_analyst(research_data)
    except Exception as e:
        observe("ERROR", f"Analyst failed: {e}")
        return f"Pipeline failed at Analysis phase: {e}"

    observe_handoff("Analyst", "Writer", len(analysis))

    # ------------------------------------------------------------------
    # Phase 3: Writing — generate the formatted report
    # ------------------------------------------------------------------
    observe_phase(3, 4, "Writing — Generating risk report")
    try:
        report = run_writer(research_data, analysis)
    except Exception as e:
        observe("ERROR", f"Writer failed: {e}")
        return f"Pipeline failed at Writing phase: {e}"

    observe_handoff("Writer", "Reviewer", len(report))

    # ------------------------------------------------------------------
    # Phase 4: Review — verify accuracy against source data
    # ------------------------------------------------------------------
    observe_phase(4, 4, "Review — Verifying accuracy")
    try:
        review = run_reviewer(report, research_data)
    except Exception as e:
        observe("ERROR", f"Reviewer failed: {e}")
        # Still return the report even if review fails
        review = "VERDICT: REVIEW_SKIPPED\nNOTES: Reviewer agent encountered an error."

    # ------------------------------------------------------------------
    # Assemble final output
    # ------------------------------------------------------------------
    elapsed = time.time() - start_time
    observe("COORDINATOR", f"Pipeline complete in {elapsed:.1f}s")

    final_output = f"""{report}

{'=' * 60}
REVIEW
{'=' * 60}
{review}

{'=' * 60}
Pipeline Stats: 4 agents | {elapsed:.1f}s total
{'=' * 60}"""

    return final_output


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    entity = sys.argv[1] if len(sys.argv) > 1 else "Acme Corporation"

    print("=" * 60)
    print("M14 Lab — Multi-Agent Content Pipeline (SOLUTION)")
    print("=" * 60)
    print(f"Entity: {entity}")
    print("=" * 60)

    result = run_pipeline(entity)

    print("\n" + "=" * 60)
    print("FINAL REPORT")
    print("=" * 60)
    print(result)
