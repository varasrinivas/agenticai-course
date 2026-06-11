"""
M20 Lab - Step 2: Feedback Collector — Closing the Loop
========================================================
Thumbs-down feedback becomes M18 eval cases automatically.
Run: python feedback_collector.py
"""

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal, Optional


@dataclass
class FeedbackRecord:
    """(COMPLETE) One user feedback event, eval-set compatible."""

    run_id: str
    query: str
    response: str
    tool_calls: list
    total_tokens: int
    thumb: Literal["up", "down"]
    user_comment: Optional[str]
    timestamp: float
    failure_category: Optional[str] = None    # e.g. "wrong_tool", "hallucinated"
    suggested_correction: Optional[str] = None


class FeedbackCollector:
    """Collects thumbs-up/down from production users; writes JSONL compatible
    with the M18 eval harness; triggers a re-eval when failures accumulate."""

    def __init__(
        self,
        feedback_path: str = "feedback/production_feedback.jsonl",
        eval_trigger_threshold: int = 20,         # trigger after N new failures
        eval_trigger_interval_seconds: int = 3600,  # but no more than once/hour
    ):
        self.feedback_path = Path(feedback_path)
        self.feedback_path.parent.mkdir(parents=True, exist_ok=True)
        self.eval_trigger_threshold = eval_trigger_threshold
        self.eval_trigger_interval = eval_trigger_interval_seconds
        self._new_failures_since_last_eval = 0
        self._last_eval_trigger_time = 0.0
        self.evals_triggered = 0  # for the test harness

    def record_feedback(self, record: FeedbackRecord) -> None:
        """TODO:
        1. Append json.dumps(asdict(record)) + "\\n" to self.feedback_path
        2. If record.thumb == "down":
             self._new_failures_since_last_eval += 1
             self._maybe_trigger_eval()
        """
        pass  # Remove this line when you add your code

    def _maybe_trigger_eval(self) -> None:
        """TODO — trigger only when BOTH conditions hold:
        - enough_failures: _new_failures_since_last_eval >= eval_trigger_threshold
        - enough_time: time.time() - _last_eval_trigger_time >= eval_trigger_interval
        (Failures alone would retrigger during a burst; time alone would fire
        on one bad day.)
        If both: print a message, self._trigger_eval_run(), reset the failure
        counter, record the trigger time.
        """
        pass  # Remove this line when you add your code

    def _trigger_eval_run(self) -> None:
        """(COMPLETE for this lab) Ingest failures + count the trigger.
        The production version shells out to pytest/CI — adapt as needed."""
        self._ingest_failures_to_eval_set()
        self.evals_triggered += 1
        print(f"  >>> EVAL RUN TRIGGERED (#{self.evals_triggered})")

    def _ingest_failures_to_eval_set(self) -> None:
        """Convert thumbs-down records into M18-compatible eval cases.

        TODO:
        1. eval_cases_path = Path("evals/data/production_failures.jsonl");
           mkdir parents
        2. Read all records from self.feedback_path (one JSON per line)
        3. failures = records where thumb == "down"
        4. Write one eval case per failure:
           {"input": r["query"],
            "reference_response": r.get("suggested_correction"),
            "source": "production_feedback",
            "run_id": r["run_id"],
            "failure_category": r.get("failure_category")}
        5. Print how many cases were ingested
        """
        pass  # Remove this line when you add your code


# ── Test harness (COMPLETE) ──
if __name__ == "__main__":
    import os
    import tempfile

    tmp = tempfile.mkdtemp()
    collector = FeedbackCollector(
        feedback_path=os.path.join(tmp, "feedback.jsonl"),
        eval_trigger_threshold=5,         # low threshold for testing
        eval_trigger_interval_seconds=0,  # no time gate for testing
    )

    print("Simulating 25 feedback events (20% thumbs-down)...")
    for i in range(25):
        thumb = "down" if i % 5 == 0 else "up"
        collector.record_feedback(FeedbackRecord(
            run_id=f"run_{i:03d}",
            query=f"Question number {i}",
            response=f"Answer number {i}",
            tool_calls=["search"] if i % 2 else [],
            total_tokens=800 + i * 10,
            thumb=thumb,
            user_comment="wrong date cited" if thumb == "down" else None,
            timestamp=time.time(),
            failure_category="hallucinated" if thumb == "down" else None,
        ))

    print(f"\nEvals triggered: {collector.evals_triggered} (expect 1 — "
          f"5 failures hit the threshold once)")
    assert collector.evals_triggered == 1

    with open(collector.feedback_path, encoding="utf-8") as f:
        n = sum(1 for line in f if line.strip())
    print(f"Feedback records written: {n} (expect 25)")
    assert n == 25

    eval_path = Path("evals/data/production_failures.jsonl")
    if eval_path.exists():
        with open(eval_path, encoding="utf-8") as f:
            cases = [json.loads(l) for l in f if l.strip()]
        print(f"Eval cases ingested: {len(cases)} (expect 5, all thumbs-down)")
        assert all(c["source"] == "production_feedback" for c in cases)

    print("\nAll feedback-loop checks passed.")
