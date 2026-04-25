"""
M18 — Eval Runner
===================
Orchestrates the full evaluation pipeline:
  1. Run all test cases through the agent (or mock agent)
  2. Score each response with all 3 scorers
  3. Generate a formatted report
  4. Save results for regression comparison

TODO: Implement the EvalRunner class and mock_agent_fn.
"""

import json
import os
import sys
from datetime import datetime, timezone

# Import the other modules from this lab
from eval_dataset import EVAL_CASES, MOCK_AGENT_RESPONSES, get_summary
from task_scorer import score_task_completion
from fuzzy_scorer import score_entity_resolution
from judge_scorer import score_with_judge


def mock_agent_fn(query: str, case_id: str = None) -> str:
    """
    Mock agent function that returns predetermined responses.
    In a real eval, this would call your actual agent from M15B.

    TODO:
    1. If case_id is provided, look up MOCK_AGENT_RESPONSES[case_id]
    2. If not found, return a generic "no response" message
    3. This function exists so students can run the full pipeline
       without needing an API key
    """
    # TODO: Implement mock agent lookup
    pass


class EvalRunner:
    """
    Runs evaluation cases through an agent and scores the results.

    TODO: Implement all methods below.
    """

    def __init__(self, mock_mode: bool = True):
        """
        Initialize the eval runner.

        Args:
            mock_mode: If True, use mock judge scores (no API calls)
        """
        self.mock_mode = mock_mode
        self.results = []

    def run_eval(
        self,
        cases: list[dict],
        agent_fn=None,
        mock_mode: bool = None,
    ) -> list[dict]:
        """
        Run all test cases through the agent and score them.

        Args:
            cases: List of test case dicts from EVAL_CASES
            agent_fn: Function(query, case_id) -> str. Defaults to mock_agent_fn.
            mock_mode: Override instance mock_mode if provided

        Returns:
            List of result dicts, one per test case:
            {
                "case_id": str,
                "category": str,
                "difficulty": str,
                "query": str,
                "response": str,
                "task_score": dict (from task_scorer),
                "entity_score": dict (from fuzzy_scorer),
                "judge_score": dict (from judge_scorer),
                "overall_score": float (average of 3 scores),
                "passed": bool (overall_score >= 0.6)
            }

        TODO:
        1. Default agent_fn to mock_agent_fn if not provided
        2. For each case:
           a. Call agent_fn(case["query"], case["id"]) to get the response
           b. Score with score_task_completion(response, case["expected"])
           c. Score with score_entity_resolution(response, case["expected"])
           d. Score with score_with_judge(query, response, expected, mock_mode)
           e. Calculate overall_score as average of the 3 scores
           f. Mark passed = True if overall_score >= 0.6
           g. Append the result dict to self.results
        3. Return self.results
        """
        # TODO: Implement eval loop
        pass

    def generate_report(self, results: list[dict] = None) -> str:
        """
        Generate a formatted evaluation report.

        Args:
            results: List of result dicts. Defaults to self.results.

        Returns:
            Formatted string report with:
            - Header with run timestamp and case count
            - Overall scores (pass/fail counts, average score)
            - Per-category breakdown table
            - Per-difficulty breakdown
            - Worst performing cases (bottom 3)
            - Full results table

        TODO:
        1. Use results or self.results
        2. Calculate aggregate stats:
           - total, passed, failed counts
           - overall average score
           - per-category averages
           - per-difficulty averages
        3. Find the 3 worst-performing cases
        4. Format everything into a readable report string
        5. Return the report string
        """
        # TODO: Implement report generation
        pass

    def save_results(self, results: list[dict] = None, filepath: str = None) -> str:
        """
        Save results to a JSON file for regression comparison.

        Args:
            results: List of result dicts. Defaults to self.results.
            filepath: Output path. Defaults to eval_results_<timestamp>.json.

        Returns:
            The filepath where results were saved.

        TODO:
        1. Use results or self.results
        2. Build a save dict with timestamp, summary stats, and full results
        3. Write to JSON file
        4. Return the filepath
        """
        # TODO: Implement save
        pass

    def compare_runs(self, current: list[dict], previous: list[dict]) -> str:
        """
        Compare two eval runs and highlight regressions.

        Args:
            current: Results from the current run
            previous: Results from a previous run

        Returns:
            Formatted comparison string showing:
            - Cases that improved
            - Cases that regressed
            - Overall score change

        TODO:
        1. Build a dict of {case_id: overall_score} for both runs
        2. For each case in current, compare against previous
        3. Flag regressions (current < previous - 0.05) and improvements
        4. Calculate overall score change
        5. Format into a readable comparison report
        """
        # TODO: Implement comparison
        pass


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
    runner = EvalRunner(mock_mode=True)
    results = runner.run_eval(EVAL_CASES, agent_fn=mock_agent_fn)

    # Step 3: Generate and print report
    report = runner.generate_report(results)
    print(report)

    # Step 4: Save results
    filepath = runner.save_results(results)
    print(f"\nResults saved to: {filepath}")

    # Step 5: Run a second time and compare (simulate regression)
    print("\n" + "=" * 60)
    print("Running comparison against saved results...")
    runner2 = EvalRunner(mock_mode=True)
    results2 = runner2.run_eval(EVAL_CASES, agent_fn=mock_agent_fn)
    comparison = runner2.compare_runs(results2, results)
    print(comparison)
