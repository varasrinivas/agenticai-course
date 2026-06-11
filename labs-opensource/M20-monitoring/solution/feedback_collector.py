"""
M20 Lab - Step 2: Feedback Collector — SOLUTION
================================================
Run: python feedback_collector.py
"""

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal, Optional


@dataclass
class FeedbackRecord:
    run_id: str
    query: str
    response: str
    tool_calls: list
    total_tokens: int
    thumb: Literal["up", "down"]
    user_comment: Optional[str]
    timestamp: float
    failure_category: Optional[str] = None
    suggested_correction: Optional[str] = None


class FeedbackCollector:
    """Collects thumbs-up/down; writes M18-compatible JSONL; triggers re-evals."""

    def __init__(
        self,
        feedback_path: str = "feedback/production_feedback.jsonl",
        eval_trigger_threshold: int = 20,
        eval_trigger_interval_seconds: int = 3600,
    ):
        self.feedback_path = Path(feedback_path)
        self.feedback_path.parent.mkdir(parents=True, exist_ok=True)
        self.eval_trigger_threshold = eval_trigger_threshold
        self.eval_trigger_interval = eval_trigger_interval_seconds
        self._new_failures_since_last_eval = 0
        self._last_eval_trigger_time = 0.0
        self.evals_triggered = 0

    def record_feedback(self, record: FeedbackRecord) -> None:
        with self.feedback_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(record)) + "\n")

        if record.thumb == "down":
            self._new_failures_since_last_eval += 1
            self._maybe_trigger_eval()

    def _maybe_trigger_eval(self) -> None:
        now = time.time()
        enough_failures = self._new_failures_since_last_eval >= self.eval_trigger_threshold
        enough_time = now - self._last_eval_trigger_time >= self.eval_trigger_interval
        # BOTH conditions: failures alone retrigger in a burst,
        # time alone fires on one bad day
        if enough_failures and enough_time:
            print(f"Triggering eval run: "
                  f"{self._new_failures_since_last_eval} new failures logged.")
            self._trigger_eval_run()
            self._new_failures_since_last_eval = 0
            self._last_eval_trigger_time = now

    def _trigger_eval_run(self) -> None:
        """Ingest failures + count the trigger. Production: shell out to CI."""
        self._ingest_failures_to_eval_set()
        self.evals_triggered += 1
        print(f"  >>> EVAL RUN TRIGGERED (#{self.evals_triggered})")

    def _ingest_failures_to_eval_set(self) -> None:
        """Convert thumbs-down records into M18-compatible eval cases."""
        eval_cases_path = Path("evals/data/production_failures.jsonl")
        eval_cases_path.parent.mkdir(parents=True, exist_ok=True)

        with self.feedback_path.open(encoding="utf-8") as f:
            records = [json.loads(line) for line in f if line.strip()]
        failures = [r for r in records if r["thumb"] == "down"]

        with eval_cases_path.open("w", encoding="utf-8") as f:
            for r in failures:
                eval_case = {
                    "input": r["query"],
                    "reference_response": r.get("suggested_correction"),
                    "source": "production_feedback",
                    "run_id": r["run_id"],
                    "failure_category": r.get("failure_category"),
                }
                f.write(json.dumps(eval_case) + "\n")
        print(f"  Ingested {len(failures)} failure cases to eval set.")


if __name__ == "__main__":
    import os
    import tempfile

    tmp = tempfile.mkdtemp()
    collector = FeedbackCollector(
        feedback_path=os.path.join(tmp, "feedback.jsonl"),
        eval_trigger_threshold=5,
        eval_trigger_interval_seconds=0,
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

    print(f"\nEvals triggered: {collector.evals_triggered} (expect 1)")
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
