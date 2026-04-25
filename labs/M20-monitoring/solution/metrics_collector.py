"""
M20 Lab — Monitoring: Metrics Collector (Solution)
===================================================
Complete implementation of the metrics collector with latency
percentiles, token costs, error rates, and per-tool statistics.

Usage:
    python metrics_collector.py
"""

import time
import random
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional


# =============================================================================
# CLAUDE SONNET PRICING (as of 2025)
# =============================================================================

SONNET_INPUT_COST_PER_MILLION = 3.00    # $3.00 per 1M input tokens
SONNET_OUTPUT_COST_PER_MILLION = 15.00  # $15.00 per 1M output tokens


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class RequestRecord:
    """Single request record with all metrics we track."""
    timestamp: float
    duration_ms: float
    input_tokens: int
    output_tokens: int
    success: bool
    tools_used: List[dict] = field(default_factory=list)


# =============================================================================
# METRICS COLLECTOR
# =============================================================================

class MetricsCollector:
    """
    Collects and aggregates metrics from agent requests.

    Tracks:
    - Request count and error rate
    - Latency percentiles (p50, p75, p90, p95, p99)
    - Token usage and cost estimates
    - Per-tool call counts, failure rates, and durations
    - Throughput (requests per minute)
    """

    def __init__(self):
        self.requests: List[RequestRecord] = []
        self.start_time: float = time.time()

    def record_request(
        self,
        duration_ms: float,
        input_tokens: int,
        output_tokens: int,
        success: bool,
        tools_used: Optional[List[dict]] = None,
    ) -> None:
        """Record a single request's metrics."""
        record = RequestRecord(
            timestamp=time.time(),
            duration_ms=duration_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            success=success,
            tools_used=tools_used or [],
        )
        self.requests.append(record)

    def get_request_count(self) -> int:
        """Return total number of recorded requests."""
        return len(self.requests)

    def get_latency_percentiles(self) -> Dict[str, float]:
        """
        Calculate latency percentiles from recorded durations.

        Returns dict with keys: p50, p75, p90, p95, p99
        """
        if not self.requests:
            return {"p50": 0, "p75": 0, "p90": 0, "p95": 0, "p99": 0}

        durations = sorted(r.duration_ms for r in self.requests)
        n = len(durations)

        def percentile(p: float) -> float:
            index = math.ceil(p / 100.0 * n) - 1
            index = max(0, min(index, n - 1))
            return durations[index]

        return {
            "p50": percentile(50),
            "p75": percentile(75),
            "p90": percentile(90),
            "p95": percentile(95),
            "p99": percentile(99),
        }

    def get_error_rate(self) -> float:
        """Calculate error rate as a percentage (0.0 to 100.0)."""
        if not self.requests:
            return 0.0
        failed = sum(1 for r in self.requests if not r.success)
        return (failed / len(self.requests)) * 100.0

    def get_token_stats(self) -> Dict[str, float]:
        """Calculate token usage statistics and cost estimates."""
        if not self.requests:
            return {
                "total_input": 0,
                "total_output": 0,
                "avg_input_per_request": 0,
                "avg_output_per_request": 0,
                "cost_estimate": 0,
                "cost_per_hour": 0,
            }

        total_input = sum(r.input_tokens for r in self.requests)
        total_output = sum(r.output_tokens for r in self.requests)
        n = len(self.requests)

        cost = (
            (total_input / 1_000_000) * SONNET_INPUT_COST_PER_MILLION
            + (total_output / 1_000_000) * SONNET_OUTPUT_COST_PER_MILLION
        )

        elapsed_hours = (time.time() - self.start_time) / 3600
        cost_per_hour = cost / elapsed_hours if elapsed_hours > 0 else 0

        return {
            "total_input": total_input,
            "total_output": total_output,
            "avg_input_per_request": total_input / n,
            "avg_output_per_request": total_output / n,
            "cost_estimate": cost,
            "cost_per_hour": cost_per_hour,
        }

    def get_tool_stats(self) -> Dict[str, Dict[str, float]]:
        """Calculate per-tool statistics."""
        tool_data: Dict[str, Dict[str, float]] = {}

        for req in self.requests:
            for tool in req.tools_used:
                name = tool["name"]
                if name not in tool_data:
                    tool_data[name] = {
                        "calls": 0,
                        "failures": 0,
                        "total_duration": 0,
                    }
                tool_data[name]["calls"] += 1
                if not tool.get("success", True):
                    tool_data[name]["failures"] += 1
                tool_data[name]["total_duration"] += tool.get("duration_ms", 0)

        result = {}
        for name, data in tool_data.items():
            calls = data["calls"]
            result[name] = {
                "calls": calls,
                "failures": data["failures"],
                "failure_rate": (data["failures"] / calls * 100) if calls > 0 else 0,
                "avg_duration_ms": (data["total_duration"] / calls) if calls > 0 else 0,
            }

        return result

    def get_throughput(self, window_minutes: int = 5) -> float:
        """Calculate requests per minute over the last N minutes."""
        cutoff = time.time() - (window_minutes * 60)
        recent = sum(1 for r in self.requests if r.timestamp >= cutoff)
        return recent / window_minutes

    def reset(self) -> None:
        """Clear all recorded metrics and reset start time."""
        self.requests = []
        self.start_time = time.time()

    def to_dict(self) -> Dict:
        """Export all metrics as a single dictionary."""
        return {
            "request_count": self.get_request_count(),
            "error_rate": self.get_error_rate(),
            "latency": self.get_latency_percentiles(),
            "tokens": self.get_token_stats(),
            "tools": self.get_tool_stats(),
            "throughput_rpm": self.get_throughput(),
            "uptime_seconds": time.time() - self.start_time,
        }


# =============================================================================
# SELF-TEST
# =============================================================================

def self_test():
    """Record 100 simulated requests and print summary stats."""
    print("=" * 60)
    print("M20 Metrics Collector — Self-Test")
    print("=" * 60)

    collector = MetricsCollector()

    tool_names = ["search_filings", "get_details", "calc_risk"]

    for i in range(100):
        if random.random() < 0.05:
            duration = random.uniform(3000, 8000)
        elif random.random() < 0.15:
            duration = random.uniform(1000, 3000)
        else:
            duration = random.uniform(100, 500)

        success = random.random() > 0.08
        input_tokens = random.randint(500, 2000)
        output_tokens = random.randint(200, 1500)

        num_tools = random.randint(1, 3)
        tools = []
        for _ in range(num_tools):
            tool_name = random.choice(tool_names)
            tool_success = random.random() > 0.05
            tool_duration = random.uniform(5, 100)
            tools.append({
                "name": tool_name,
                "duration_ms": tool_duration,
                "success": tool_success,
            })

        collector.record_request(duration, input_tokens, output_tokens, success, tools)

    print(f"\nRequests recorded: {collector.get_request_count()}")
    print(f"Error rate: {collector.get_error_rate():.1f}%")

    latency = collector.get_latency_percentiles()
    print(f"\nLatency percentiles (ms):")
    for key in ["p50", "p75", "p90", "p95", "p99"]:
        print(f"  {key}: {latency[key]:.0f}")

    tokens = collector.get_token_stats()
    print(f"\nToken stats:")
    print(f"  Total input:  {tokens['total_input']:,}")
    print(f"  Total output: {tokens['total_output']:,}")
    print(f"  Cost estimate: ${tokens['cost_estimate']:.4f}")

    tools = collector.get_tool_stats()
    print(f"\nTool stats:")
    for name, stats in tools.items():
        print(f"  {name}: {stats['calls']} calls, "
              f"{stats['failure_rate']:.1f}% fail, "
              f"avg {stats['avg_duration_ms']:.0f}ms")

    print(f"\nThroughput: {collector.get_throughput():.1f} req/min")

    assert latency["p50"] <= latency["p75"] <= latency["p90"] <= latency["p95"] <= latency["p99"], \
        "Percentiles should be monotonically increasing!"
    print("\n✅ Percentiles are monotonically increasing — PASS")

    print(f"\n{'=' * 60}")
    print("Self-test complete!")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    self_test()
