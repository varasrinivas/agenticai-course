"""
Evaluation Harness — runs test cases against the agent system.
(Solution — fully implemented)
"""

import json
import os
import time
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class TestResult:
    test_id: str
    category: str
    difficulty: str
    passed: bool
    tool_call_score: float
    output_score: float
    combined_score: float
    expected_tool_calls: List[str]
    actual_tool_calls: List[str]
    expected_output_contains: List[str]
    actual_output: str
    latency_ms: float
    error: Optional[str] = None


@dataclass
class EvalReport:
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
    """Runs a suite of test cases against the agent system."""

    def __init__(self, test_cases_path: Optional[str] = None):
        if test_cases_path is None:
            test_cases_path = os.path.join(
                os.path.dirname(__file__), "test_cases.json"
            )
        self._test_cases = self._load_test_cases(test_cases_path)
        self._results: List[TestResult] = []

    def _load_test_cases(self, path: str) -> List[Dict[str, Any]]:
        with open(path, "r") as f:
            data = json.load(f)
        return data.get("test_cases", data) if isinstance(data, dict) else data

    def score_tool_calls(self, expected: List[str], actual: List[str]) -> float:
        if not expected:
            return 1.0
        expected_set = {t.lower() for t in expected}
        actual_set = {t.lower() for t in actual}
        overlap = len(expected_set & actual_set)
        return overlap / len(expected_set)

    def score_output(self, expected_contains: List[str], actual_output: str) -> float:
        if not expected_contains:
            return 1.0
        output_lower = actual_output.lower()
        found = sum(1 for phrase in expected_contains if phrase.lower() in output_lower)
        return found / len(expected_contains)

    def run_single_test(self, test_case: Dict[str, Any], agent_fn) -> TestResult:
        test_id = test_case.get("id", "unknown")
        category = test_case.get("category", "unknown")
        difficulty = test_case.get("difficulty", "unknown")
        query = test_case.get("query", "")
        expected_tools = test_case.get("expected_tool_calls", [])
        expected_output = test_case.get("expected_output_contains", [])

        start = time.time()
        error = None
        actual_output = ""
        actual_tools = []

        try:
            result = agent_fn(query)
            if result:
                actual_output = result.get("answer", "")
                actual_tools = [tc.get("name", "") for tc in result.get("tool_calls_made", [])]
                # Also check tool_calls key
                if not actual_tools and "tool_calls" in result:
                    actual_tools = result["tool_calls"]
        except Exception as e:
            error = str(e)
            actual_output = f"ERROR: {e}"

        elapsed = (time.time() - start) * 1000

        tool_score = self.score_tool_calls(expected_tools, actual_tools)
        output_score = self.score_output(expected_output, actual_output)
        combined = 0.4 * tool_score + 0.6 * output_score
        passed = combined >= 0.6 and error is None

        return TestResult(
            test_id=test_id, category=category, difficulty=difficulty,
            passed=passed, tool_call_score=tool_score, output_score=output_score,
            combined_score=combined,
            expected_tool_calls=expected_tools, actual_tool_calls=actual_tools,
            expected_output_contains=expected_output, actual_output=actual_output[:500],
            latency_ms=elapsed, error=error,
        )

    def run_all(
        self, agent_fn, category: Optional[str] = None,
        difficulty: Optional[str] = None, max_tests: Optional[int] = None,
    ) -> EvalReport:
        tests = self._test_cases
        if category:
            tests = [t for t in tests if t.get("category") == category]
        if difficulty:
            tests = [t for t in tests if t.get("difficulty") == difficulty]
        if max_tests:
            tests = tests[:max_tests]

        results = []
        for i, tc in enumerate(tests):
            print(f"  Running test {i + 1}/{len(tests)}: {tc.get('id', '?')}...", end="", flush=True)
            result = self.run_single_test(tc, agent_fn)
            results.append(result)
            status = "PASS" if result.passed else "FAIL"
            print(f" {status} (score={result.combined_score:.2f}, {result.latency_ms:.0f}ms)")

        self._results = results

        # Aggregate
        passed = sum(1 for r in results if r.passed)
        failed = len(results) - passed
        accuracy = passed / len(results) if results else 0.0

        # By category
        by_cat = {}
        for r in results:
            if r.category not in by_cat:
                by_cat[r.category] = {"passed": 0, "total": 0}
            by_cat[r.category]["total"] += 1
            if r.passed:
                by_cat[r.category]["passed"] += 1
        accuracy_by_cat = {c: d["passed"] / d["total"] for c, d in by_cat.items()}

        # By difficulty
        by_diff = {}
        for r in results:
            if r.difficulty not in by_diff:
                by_diff[r.difficulty] = {"passed": 0, "total": 0}
            by_diff[r.difficulty]["total"] += 1
            if r.passed:
                by_diff[r.difficulty]["passed"] += 1
        accuracy_by_diff = {d: v["passed"] / v["total"] for d, v in by_diff.items()}

        avg_latency = sum(r.latency_ms for r in results) / len(results) if results else 0.0
        avg_tool = sum(r.tool_call_score for r in results) / len(results) if results else 0.0
        avg_out = sum(r.output_score for r in results) / len(results) if results else 0.0

        return EvalReport(
            total_tests=len(results), passed=passed, failed=failed,
            overall_accuracy=accuracy, accuracy_by_category=accuracy_by_cat,
            accuracy_by_difficulty=accuracy_by_diff, avg_latency_ms=avg_latency,
            avg_tool_call_score=avg_tool, avg_output_score=avg_out, results=results,
        )

    def format_report(self, report: EvalReport) -> str:
        lines = ["=" * 60]
        lines.append("  EVALUATION REPORT")
        lines.append("=" * 60)
        lines.append(f"  Total Tests: {report.total_tests}")
        lines.append(f"  Passed: {report.passed}  |  Failed: {report.failed}")
        lines.append(f"  Overall Accuracy: {report.overall_accuracy * 100:.1f}%")
        lines.append("")
        lines.append("  Accuracy by Category:")
        for cat, acc in sorted(report.accuracy_by_category.items()):
            lines.append(f"    {cat:25s} {acc * 100:5.1f}%")
        lines.append("")
        lines.append("  Accuracy by Difficulty:")
        for diff, acc in sorted(report.accuracy_by_difficulty.items()):
            lines.append(f"    {diff:25s} {acc * 100:5.1f}%")
        lines.append("")
        lines.append(f"  Avg Latency: {report.avg_latency_ms:.0f}ms")
        lines.append(f"  Avg Tool Call Score: {report.avg_tool_call_score:.2f}")
        lines.append(f"  Avg Output Score: {report.avg_output_score:.2f}")

        # Top failures
        failures = [r for r in report.results if not r.passed]
        if failures:
            lines.append("")
            lines.append("  Top Failures:")
            for r in failures[:5]:
                lines.append(f"    [{r.test_id}] score={r.combined_score:.2f} "
                             f"tools={r.tool_call_score:.2f} output={r.output_score:.2f}")
                if r.error:
                    lines.append(f"      Error: {r.error[:80]}")

        lines.append("=" * 60)
        return "\n".join(lines)

    @property
    def test_cases(self) -> List[Dict[str, Any]]:
        return self._test_cases

    @property
    def test_count(self) -> int:
        return len(self._test_cases)
