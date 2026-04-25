"""
M20 Lab — Monitoring: Metrics Collector (Starter)
==================================================
Build a metrics collector that tracks request count, latency
percentiles, token costs, error rates, and per-tool statistics
for a UCC filing agent.

KEY CONCEPT: Raw logs are noise. Metrics are signal. A good
collector turns thousands of individual requests into a handful
of numbers (p95 latency, error rate, cost/hour) that tell you
whether your agent is healthy or sick.

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
# WHAT: Cost per token for Claude Sonnet model
# WHY:  We need real pricing to estimate costs accurately
# GOTCHA: Prices change — check docs.anthropic.com for current rates

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
    # tools_used format: [{"name": "search_filings", "duration_ms": 45, "success": True}]


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
        """
        Record a single request's metrics.

        Args:
            duration_ms: How long the request took in milliseconds
            input_tokens: Number of input tokens consumed
            output_tokens: Number of output tokens generated
            success: Whether the request completed successfully
            tools_used: List of tool calls, each with name, duration_ms, success
        """
        # TODO: Create a RequestRecord and append it to self.requests
        # HINT: Use time.time() for the timestamp
        # HINT: Use tools_used or [] if None
        pass

    def get_request_count(self) -> int:
        """Return total number of recorded requests."""
        # TODO: Return the length of self.requests
        pass

    def get_latency_percentiles(self) -> Dict[str, float]:
        """
        Calculate latency percentiles from recorded durations.

        Returns dict with keys: p50, p75, p90, p95, p99
        Each value is the latency in milliseconds at that percentile.

        Algorithm:
        1. Sort all durations
        2. For percentile P, find index = ceil(P/100 * N) - 1
        3. Return the value at that index
        """
        # TODO: Implement percentile calculation
        # HINT: Extract all duration_ms values into a sorted list
        # HINT: For each percentile, calculate the index:
        #   index = ceil(percentile / 100 * len(sorted_durations)) - 1
        # HINT: Clamp index to valid range [0, len-1]
        # HINT: Return {"p50": ..., "p75": ..., "p90": ..., "p95": ..., "p99": ...}
        # HINT: If no requests, return all zeros
        pass

    def get_error_rate(self) -> float:
        """
        Calculate error rate as a percentage.

        Returns: float between 0.0 and 100.0
        """
        # TODO: Count failed requests (success=False) / total requests * 100
        # HINT: Return 0.0 if no requests recorded
        pass

    def get_token_stats(self) -> Dict[str, float]:
        """
        Calculate token usage statistics and cost estimates.

        Returns dict with keys:
        - total_input: total input tokens across all requests
        - total_output: total output tokens across all requests
        - avg_input_per_request: average input tokens per request
        - avg_output_per_request: average output tokens per request
        - cost_estimate: total cost in dollars using Sonnet pricing
        - cost_per_hour: projected hourly cost based on elapsed time
        """
        # TODO: Implement token statistics
        # HINT: Sum up all input_tokens and output_tokens
        # HINT: cost = (total_input / 1_000_000 * SONNET_INPUT_COST_PER_MILLION)
        #             + (total_output / 1_000_000 * SONNET_OUTPUT_COST_PER_MILLION)
        # HINT: cost_per_hour = cost / elapsed_hours (use time.time() - self.start_time)
        # HINT: Return all zeros if no requests
        pass

    def get_tool_stats(self) -> Dict[str, Dict[str, float]]:
        """
        Calculate per-tool statistics.

        Returns dict like:
        {
            "search_filings": {
                "calls": 847,
                "failures": 10,
                "failure_rate": 1.18,
                "avg_duration_ms": 45.2
            },
            ...
        }
        """
        # TODO: Iterate through all requests and their tools_used
        # HINT: Build a dict keyed by tool name
        # HINT: Track total calls, failures, and sum of durations per tool
        # HINT: Calculate failure_rate = failures / calls * 100
        # HINT: Calculate avg_duration_ms = total_duration / calls
        pass

    def get_throughput(self, window_minutes: int = 5) -> float:
        """
        Calculate requests per minute over the last N minutes.

        Args:
            window_minutes: How far back to look (default 5 minutes)

        Returns: requests per minute as a float
        """
        # TODO: Count requests in the last window_minutes
        # HINT: cutoff = time.time() - (window_minutes * 60)
        # HINT: Count requests with timestamp >= cutoff
        # HINT: Return count / window_minutes
        pass

    def reset(self) -> None:
        """Clear all recorded metrics and reset start time."""
        # TODO: Clear self.requests and reset self.start_time
        pass

    def to_dict(self) -> Dict:
        """Export all metrics as a single dictionary."""
        # TODO: Return a dict combining all metrics:
        # {
        #     "request_count": ...,
        #     "error_rate": ...,
        #     "latency": self.get_latency_percentiles(),
        #     "tokens": self.get_token_stats(),
        #     "tools": self.get_tool_stats(),
        #     "throughput_rpm": self.get_throughput(),
        #     "uptime_seconds": time.time() - self.start_time,
        # }
        pass


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

    # Simulate 100 requests with realistic distributions
    for i in range(100):
        # Most requests are fast (100-500ms), some slow (1000-5000ms), few very slow
        if random.random() < 0.05:
            duration = random.uniform(3000, 8000)  # 5% very slow
        elif random.random() < 0.15:
            duration = random.uniform(1000, 3000)  # 15% slow
        else:
            duration = random.uniform(100, 500)     # 80% normal

        # Most succeed, ~8% fail
        success = random.random() > 0.08

        # Token counts vary
        input_tokens = random.randint(500, 2000)
        output_tokens = random.randint(200, 1500)

        # 1-3 tools per request
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

    # Print results
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

    # Verify monotonic percentiles
    assert latency["p50"] <= latency["p75"] <= latency["p90"] <= latency["p95"] <= latency["p99"], \
        "Percentiles should be monotonically increasing!"
    print("\n✅ Percentiles are monotonically increasing — PASS")

    print(f"\n{'=' * 60}")
    print("Self-test complete!")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    self_test()
