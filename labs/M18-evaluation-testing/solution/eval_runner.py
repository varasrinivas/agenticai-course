"""
M18 — Eval Runner (Solution)
===============================
Orchestrates the full evaluation pipeline:
  1. Run all test cases through the agent (or mock agent)
  2. Score each response with all 3 scorers
  3. Generate a formatted report
  4. Save results for regression comparison
"""

import json
import os
import sys
from datetime import datetime, timezone

from eval_dataset import EVAL_CASES, MOCK_AGENT_RESPONSES, get_summary
from task_scorer import score_task_completion
from fuzzy_scorer import score_entity_resolution
from judge_scorer import score_with_judge


def mock_agent_fn(query: str, case_id: str = None) -> str:
    """
    Mock agent function that returns predetermined responses.
    In a real eval, this would call your actual agent from M15B.
    """
    if case_id and case_id in MOCK_AGENT_RESPONSES:
        return MOCK_AGENT_RESPONSES[case_id]
    return "I was unable to find any relevant information for your query."


class EvalRunner:
    """Runs evaluation cases through an agent and scores the results."""

    def __init__(self, mock_mode: bool = True):
        self.mock_mode = mock_mode
        self.results = []

    def run_eval(
        self,
        cases: list[dict],
        agent_fn=None,
        mock_mode: bool = None,
    ) -> list[dict]:
        """Run all test cases through the agent and score them."""
        if agent_fn is None:
            agent_fn = mock_agent_fn
        if mock_mode is None:
            mock_mode = self.mock_mode

        self.results = []

        for i, case in enumerate(cases):
            case_id = case["id"]
            query = case["query"]
            expected = case["expected"]

            # Step 1: Get agent response
            response = agent_fn(query, case_id)

            # Step 2: Score with all 3 scorers
            task_result = score_task_completion(response, expected)
            entity_result = score_entity_resolution(response, expected)
            judge_result = score_with_judge(query, response, expected, mock_mode=mock_mode)

            # Step 3: Calculate overall score (average of 3)
            overall = (
                task_result["score"]
                + entity_result["score"]
                + judge_result["score"]
            ) / 3.0

            result = {
                "case_id": case_id,
                "category": case["category"],
                "difficulty": case["difficulty"],
                "query": query,
                "response": response,
                "task_score": task_result,
                "entity_score": entity_result,
                "judge_score": judge_result,
                "overall_score": round(overall, 3),
                "passed": overall >= 0.6,
            }

            self.results.append(result)
            status = "PASS" if result["passed"] else "FAIL"
            print(
                f"  [{i+1:2d}/{len(cases)}] {case_id:6s} {status}  "
                f"task={task_result['score']:.2f}  "
                f"entity={entity_result['score']:.2f}  "
                f"judge={judge_result['score']:.2f}  "
                f"overall={overall:.2f}"
            )

        return self.results

    def generate_report(self, results: list[dict] = None) -> str:
        """Generate a formatted evaluation report."""
        if results is None:
            results = self.results

        if not results:
            return "No results to report."

        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        run_id = f"eval-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"

        total = len(results)
        passed = sum(1 for r in results if r["passed"])
        failed = total - passed
        avg_score = sum(r["overall_score"] for r in results) / total

        avg_task = sum(r["task_score"]["score"] for r in results) / total
        avg_entity = sum(r["entity_score"]["score"] for r in results) / total
        avg_judge = sum(r["judge_score"]["score"] for r in results) / total

        lines = []
        lines.append("")
        lines.append("=" * 55)
        lines.append("  UCC Research Agent — Evaluation Report")
        lines.append("=" * 55)
        lines.append(f"  Run ID:    {run_id}")
        lines.append(f"  Date:      {now}")
        lines.append(f"  Cases:     {total}  |  Pass: {passed}  |  Fail: {failed}")
        lines.append(f"  Overall:   {avg_score:.3f}")
        lines.append(f"  Threshold: 0.600 (pass/fail cutoff)")
        lines.append("")

        # --- Scorer breakdown ---
        lines.append("-" * 55)
        lines.append("  Scorer Averages")
        lines.append("-" * 55)
        lines.append(f"  {'Scorer':<25s} {'Avg Score':>10s}")
        lines.append(f"  {'-' * 25} {'-' * 10}")
        lines.append(f"  {'Task Completion':<25s} {avg_task:>10.3f}")
        lines.append(f"  {'Entity Resolution':<25s} {avg_entity:>10.3f}")
        lines.append(f"  {'Claude-as-Judge':<25s} {avg_judge:>10.3f}")
        lines.append("")

        # --- Per-category breakdown ---
        categories = {}
        for r in results:
            cat = r["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(r)

        lines.append("-" * 55)
        lines.append("  Per-Category Breakdown")
        lines.append("-" * 55)
        lines.append(f"  {'Category':<25s} {'Cases':>6s} {'Pass':>6s} {'Avg':>8s}")
        lines.append(f"  {'-' * 25} {'-' * 6} {'-' * 6} {'-' * 8}")

        for cat in sorted(categories.keys()):
            cat_results = categories[cat]
            cat_total = len(cat_results)
            cat_passed = sum(1 for r in cat_results if r["passed"])
            cat_avg = sum(r["overall_score"] for r in cat_results) / cat_total
            lines.append(
                f"  {cat:<25s} {cat_total:>6d} {cat_passed:>6d} {cat_avg:>8.3f}"
            )
        lines.append("")

        # --- Per-difficulty breakdown ---
        difficulties = {}
        for r in results:
            diff = r["difficulty"]
            if diff not in difficulties:
                difficulties[diff] = []
            difficulties[diff].append(r)

        lines.append("-" * 55)
        lines.append("  Per-Difficulty Breakdown")
        lines.append("-" * 55)
        lines.append(f"  {'Difficulty':<25s} {'Cases':>6s} {'Pass':>6s} {'Avg':>8s}")
        lines.append(f"  {'-' * 25} {'-' * 6} {'-' * 6} {'-' * 8}")

        for diff in ["easy", "medium", "hard"]:
            if diff in difficulties:
                diff_results = difficulties[diff]
                diff_total = len(diff_results)
                diff_passed = sum(1 for r in diff_results if r["passed"])
                diff_avg = sum(r["overall_score"] for r in diff_results) / diff_total
                lines.append(
                    f"  {diff:<25s} {diff_total:>6d} {diff_passed:>6d} {diff_avg:>8.3f}"
                )
        lines.append("")

        # --- Worst performers ---
        sorted_results = sorted(results, key=lambda r: r["overall_score"])
        worst = sorted_results[:3]

        lines.append("-" * 55)
        lines.append("  Worst Performing Cases")
        lines.append("-" * 55)
        for r in worst:
            lines.append(
                f"  {r['case_id']:6s}  score={r['overall_score']:.3f}  "
                f"({r['category']}, {r['difficulty']})"
            )
            lines.append(f"         query: {r['query'][:50]}...")
            if r["task_score"]["missed"]:
                lines.append(f"         missed filings: {r['task_score']['missed']}")
        lines.append("")

        # --- Full results table ---
        lines.append("-" * 55)
        lines.append("  Full Results")
        lines.append("-" * 55)
        lines.append(
            f"  {'ID':<7s} {'Cat':<18s} {'Diff':<7s} "
            f"{'Task':>5s} {'Ent':>5s} {'Jdg':>5s} {'All':>5s} {'P/F':>4s}"
        )
        lines.append(
            f"  {'-' * 6} {'-' * 17} {'-' * 6} "
            f"{'-' * 5} {'-' * 5} {'-' * 5} {'-' * 5} {'-' * 4}"
        )
        for r in results:
            pf = "PASS" if r["passed"] else "FAIL"
            lines.append(
                f"  {r['case_id']:<7s} {r['category']:<18s} {r['difficulty']:<7s} "
                f"{r['task_score']['score']:>5.2f} "
                f"{r['entity_score']['score']:>5.2f} "
                f"{r['judge_score']['score']:>5.2f} "
                f"{r['overall_score']:>5.2f} "
                f"{pf:>4s}"
            )

        lines.append("")
        lines.append("=" * 55)

        return "\n".join(lines)

    def save_results(self, results: list[dict] = None, filepath: str = None) -> str:
        """Save results to JSON for regression comparison."""
        if results is None:
            results = self.results

        if filepath is None:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            filepath = f"eval_results_{timestamp}.json"

        total = len(results)
        passed = sum(1 for r in results if r["passed"])
        avg_score = sum(r["overall_score"] for r in results) / total if total else 0

        save_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "total": total,
                "passed": passed,
                "failed": total - passed,
                "average_score": round(avg_score, 3),
            },
            "results": [
                {
                    "case_id": r["case_id"],
                    "category": r["category"],
                    "difficulty": r["difficulty"],
                    "overall_score": r["overall_score"],
                    "task_score": r["task_score"]["score"],
                    "entity_score": r["entity_score"]["score"],
                    "judge_score": r["judge_score"]["score"],
                    "passed": r["passed"],
                }
                for r in results
            ],
        }

        with open(filepath, "w") as f:
            json.dump(save_data, f, indent=2)

        return filepath

    def compare_runs(self, current: list[dict], previous: list[dict]) -> str:
        """Compare two eval runs and highlight regressions."""
        # Build lookup dicts
        current_scores = {r["case_id"]: r["overall_score"] for r in current}
        previous_scores = {r["case_id"]: r["overall_score"] for r in previous}

        improvements = []
        regressions = []
        unchanged = []

        for case_id in current_scores:
            if case_id not in previous_scores:
                continue
            curr = current_scores[case_id]
            prev = previous_scores[case_id]
            diff = curr - prev

            if diff > 0.05:
                improvements.append((case_id, prev, curr, diff))
            elif diff < -0.05:
                regressions.append((case_id, prev, curr, diff))
            else:
                unchanged.append((case_id, prev, curr))

        curr_avg = sum(current_scores.values()) / len(current_scores) if current_scores else 0
        prev_avg = sum(previous_scores.values()) / len(previous_scores) if previous_scores else 0
        avg_diff = curr_avg - prev_avg

        lines = []
        lines.append("")
        lines.append("-" * 55)
        lines.append("  Regression Comparison")
        lines.append("-" * 55)
        lines.append(f"  Previous avg: {prev_avg:.3f}")
        lines.append(f"  Current avg:  {curr_avg:.3f}")
        lines.append(f"  Change:       {avg_diff:+.3f}")
        lines.append("")

        if regressions:
            lines.append(f"  REGRESSIONS ({len(regressions)}):")
            for case_id, prev, curr, diff in sorted(regressions, key=lambda x: x[3]):
                lines.append(f"    {case_id}: {prev:.3f} -> {curr:.3f} ({diff:+.3f})")
        else:
            lines.append("  No regressions detected.")

        if improvements:
            lines.append(f"\n  IMPROVEMENTS ({len(improvements)}):")
            for case_id, prev, curr, diff in sorted(improvements, key=lambda x: -x[3]):
                lines.append(f"    {case_id}: {prev:.3f} -> {curr:.3f} ({diff:+.3f})")

        lines.append(f"\n  Unchanged: {len(unchanged)} cases")
        lines.append("-" * 55)

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Self-test: Run full eval pipeline in mock mode
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("M18 Eval Runner — Full Pipeline Test")
    print("=" * 60)

    # Step 1: Show dataset summary
    summary = get_summary()
    print(f"\nDataset: {summary['total_cases']} cases")
    for cat, count in sorted(summary["categories"].items()):
        print(f"  {cat}: {count}")

    # Step 2: Run eval
    print(f"\nRunning evaluation...")
    runner = EvalRunner(mock_mode=True)
    results = runner.run_eval(EVAL_CASES, agent_fn=mock_agent_fn)

    # Step 3: Generate and print report
    report = runner.generate_report(results)
    print(report)

    # Step 4: Save results
    filepath = runner.save_results(results)
    print(f"\nResults saved to: {filepath}")

    # Step 5: Comparison (same run = no regressions)
    print("\n" + "=" * 60)
    print("Running comparison against saved results...")
    runner2 = EvalRunner(mock_mode=True)
    results2 = runner2.run_eval(EVAL_CASES, agent_fn=mock_agent_fn)
    comparison = runner2.compare_runs(results2, results)
    print(comparison)
