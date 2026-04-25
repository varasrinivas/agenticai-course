"""
Evaluation Harness — runs test cases against the agent system.

Supports:
- Loading test cases from test_cases.json
- Running each test case through the agent
- Scoring: exact match on tool calls, fuzzy match on output content
- Per-category accuracy reporting
- Overall pass/fail with detailed results
"""

import json
import os
import time
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class TestResult:
    """Result of running a single test case."""
    test_id: str
    category: str
    difficulty: str
    passed: bool
    tool_call_score: float       # 0.0-1.0 (exact match on expected tool calls)
    output_score: float          # 0.0-1.0 (fuzzy match on expected output content)
    combined_score: float        # weighted average
    expected_tool_calls: List[str]
    actual_tool_calls: List[str]
    expected_output_contains: List[str]
    actual_output: str
    latency_ms: float
    error: Optional[str] = None


@dataclass
class EvalReport:
    """Aggregated evaluation report."""
    total_tests: int
    passed: int
    failed: int
    overall_accuracy: float
    accuracy_by_category: Dict[str, float]
    accuracy_by_difficulty: Dict[str, float]
    avg_latency_ms: float
    avg_tool_call_score: float
    avg_output_score: float
    results: List[TestResult]


class EvaluationHarness:
    """
    Runs a suite of test cases against the agent system.

    Each test case specifies:
    - input query
    - expected tool calls (which tools should be called)
    - expected output content (phrases that should appear in the answer)
    - difficulty level
    - category
    """

    def __init__(self, test_cases_path: Optional[str] = None):
        if test_cases_path is None:
            test_cases_path = os.path.join(
                os.path.dirname(__file__), "test_cases.json"
            )
        self._test_cases = self._load_test_cases(test_cases_path)
        self._results: List[TestResult] = []

    def _load_test_cases(self, path: str) -> List[Dict[str, Any]]:
        """Load test cases from JSON file."""
        with open(path, "r") as f:
            data = json.load(f)
        return data.get("test_cases", data) if isinstance(data, dict) else data

    # ------------------------------------------------------------------
    # TODO 1: Implement score_tool_calls()
    # Compare expected tool calls to actual tool calls.
    # Score = |expected ∩ actual| / |expected|
    # If expected is empty, return 1.0 (no tools expected).
    # Tool names should be compared case-insensitively.
    # ------------------------------------------------------------------
    def score_tool_calls(
        self,
        expected: List[str],
        actual: List[str],
    ) -> float:
        """Score tool call accuracy."""
        # TODO: Compute tool call overlap score
        pass

    # ------------------------------------------------------------------
    # TODO 2: Implement score_output()
    # Check how many expected phrases appear in the actual output.
    # Score = (phrases found) / (total expected phrases)
    # Case-insensitive matching.
    # If expected_contains is empty, return 1.0.
    # ------------------------------------------------------------------
    def score_output(
        self,
        expected_contains: List[str],
        actual_output: str,
    ) -> float:
        """Score output content accuracy."""
        # TODO: Check which expected phrases appear in output
        pass

    # ------------------------------------------------------------------
    # TODO 3: Implement run_single_test()
    # Run a single test case against the agent system.
    # Parameters:
    #   - test_case: dict from test_cases.json
    #   - agent_fn: callable that takes a query string and returns
    #     {"answer": str, "tool_calls_made": [{"name": str, ...}]}
    # Steps:
    #   1. Extract query, expected_tool_calls, expected_output_contains
    #   2. Start timer
    #   3. Call agent_fn(query) — wrap in try/except
    #   4. Stop timer
    #   5. Extract actual tool call names from result
    #   6. Score tool calls and output
    #   7. Compute combined_score = 0.4 * tool_score + 0.6 * output_score
    #   8. Pass if combined_score >= 0.6
    #   9. Return TestResult
    # ------------------------------------------------------------------
    def run_single_test(
        self,
        test_case: Dict[str, Any],
        agent_fn,
    ) -> TestResult:
        """Run a single test case."""
        # TODO: Execute test and compute scores
        pass

    # ------------------------------------------------------------------
    # TODO 4: Implement run_all()
    # Run all test cases (or a subset by category/difficulty).
    # Parameters:
    #   - agent_fn: the callable to test
    #   - category: optional filter (e.g., "filing_lookup")
    #   - difficulty: optional filter (e.g., "simple")
    #   - max_tests: optional limit on number of tests to run
    # Returns an EvalReport with aggregated results.
    # ------------------------------------------------------------------
    def run_all(
        self,
        agent_fn,
        category: Optional[str] = None,
        difficulty: Optional[str] = None,
        max_tests: Optional[int] = None,
    ) -> EvalReport:
        """Run all (or filtered) test cases and return aggregated report."""
        # TODO: Filter tests, run each, aggregate results
        pass

    # ------------------------------------------------------------------
    # TODO 5: Implement format_report()
    # Format an EvalReport as a human-readable string.
    # Include:
    #   - Overall accuracy
    #   - Accuracy by category
    #   - Accuracy by difficulty
    #   - Top failures (show first 5 failed tests with details)
    #   - Average latency
    # ------------------------------------------------------------------
    def format_report(self, report: EvalReport) -> str:
        """Format evaluation report as readable string."""
        # TODO: Build formatted report string
        pass

    @property
    def test_cases(self) -> List[Dict[str, Any]]:
        """Return loaded test cases."""
        return self._test_cases

    @property
    def test_count(self) -> int:
        """Return number of test cases."""
        return len(self._test_cases)
