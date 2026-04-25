"""
Metrics Collector — cost, latency, and token usage tracking.

Tracks:
- Per-request cost (broken down by model tier)
- Latency percentiles (p50, p95, p99)
- Token usage by model
- Request counts by type and status
"""

import time
import statistics
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime


@dataclass
class RequestMetric:
    """Metrics for a single request."""
    request_id: str
    task_type: str
    model_tier: str
    model_id: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_usd: float
    latency_ms: float
    status: str            # "success", "error"
    timestamp: str
    tool_calls: int = 0
    agent_handoffs: int = 0


class MetricsCollector:
    """
    Collects and reports on system metrics.

    Provides:
    - Real-time cost tracking per request
    - Latency percentile calculations
    - Token usage aggregation by model tier
    - Dashboard-style console output
    """

    def __init__(self):
        self._metrics: List[RequestMetric] = []
        self._cost_by_tier: Dict[str, float] = {"fast": 0.0, "balanced": 0.0, "powerful": 0.0}
        self._tokens_by_tier: Dict[str, Dict[str, int]] = {
            "fast": {"input": 0, "output": 0},
            "balanced": {"input": 0, "output": 0},
            "powerful": {"input": 0, "output": 0},
        }

    # ------------------------------------------------------------------
    # TODO 1: Implement record()
    # Record a request metric. Steps:
    #   1. Create a RequestMetric from the given parameters
    #   2. Append to self._metrics
    #   3. Update self._cost_by_tier[model_tier] += cost_usd
    #   4. Update self._tokens_by_tier[model_tier] input/output
    # ------------------------------------------------------------------
    def record(
        self,
        request_id: str,
        task_type: str,
        model_tier: str,
        model_id: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
        latency_ms: float,
        status: str = "success",
        tool_calls: int = 0,
        agent_handoffs: int = 0,
    ) -> None:
        """Record metrics for a completed request."""
        # TODO: Create RequestMetric and update aggregates
        pass

    # ------------------------------------------------------------------
    # TODO 2: Implement get_cost_report()
    # Return a cost breakdown:
    #   - total_cost_usd: sum across all tiers
    #   - cost_by_tier: {tier: cost}
    #   - cost_per_request_avg: total / count (or 0 if no requests)
    #   - most_expensive_tier: tier with highest total cost
    #   - request_count: total requests
    # ------------------------------------------------------------------
    def get_cost_report(self) -> Dict[str, Any]:
        """Generate a cost report."""
        # TODO: Compute cost breakdown
        pass

    # ------------------------------------------------------------------
    # TODO 3: Implement get_latency_percentiles()
    # Compute latency percentiles from all recorded metrics.
    # Return: {"p50": float, "p95": float, "p99": float,
    #          "mean": float, "min": float, "max": float}
    # Use statistics module. Handle case of 0 or 1 metrics.
    # Optionally filter by task_type if provided.
    # ------------------------------------------------------------------
    def get_latency_percentiles(
        self, task_type: Optional[str] = None,
    ) -> Dict[str, float]:
        """Compute latency percentiles."""
        # TODO: Compute percentiles using statistics.quantiles
        pass

    # ------------------------------------------------------------------
    # TODO 4: Implement get_token_usage()
    # Return token usage summary:
    #   - total_input_tokens, total_output_tokens, total_tokens
    #   - tokens_by_tier: {tier: {input, output, total}}
    #   - avg_tokens_per_request
    # ------------------------------------------------------------------
    def get_token_usage(self) -> Dict[str, Any]:
        """Get token usage summary."""
        # TODO: Aggregate token usage data
        pass

    # ------------------------------------------------------------------
    # TODO 5: Implement get_request_stats()
    # Return request statistics:
    #   - total_requests
    #   - requests_by_type: {task_type: count}
    #   - requests_by_status: {"success": count, "error": count}
    #   - success_rate: successes / total
    #   - avg_tool_calls_per_request
    # ------------------------------------------------------------------
    def get_request_stats(self) -> Dict[str, Any]:
        """Get request statistics."""
        # TODO: Compute request stats
        pass

    # ------------------------------------------------------------------
    # TODO 6: Implement format_dashboard()
    # Generate a console dashboard string. Include sections for:
    #   1. Request Summary (count, success rate)
    #   2. Cost Breakdown (by tier, total)
    #   3. Latency Percentiles
    #   4. Token Usage (by tier)
    # Use box-drawing characters for visual formatting.
    # Example output:
    # ┌─────────────────────────────────────────────┐
    # │         UCC PRODUCTION AGENT DASHBOARD       │
    # ├─────────────────────────────────────────────┤
    # │ Requests: 47  |  Success Rate: 95.7%        │
    # │ Total Cost: $0.1842  |  Avg: $0.0039/req    │
    # ├─────────────────────────────────────────────┤
    # │ Cost by Tier:                                │
    # │   fast:     $0.0234  (15 requests)           │
    # │   balanced: $0.0891  (22 requests)           │
    # │   powerful: $0.0717  (10 requests)           │
    # ├─────────────────────────────────────────────┤
    # │ Latency:                                     │
    # │   p50: 234ms  p95: 891ms  p99: 1523ms       │
    # └─────────────────────────────────────────────┘
    # ------------------------------------------------------------------
    def format_dashboard(self) -> str:
        """Generate a console dashboard string."""
        # TODO: Build formatted dashboard string
        pass

    def __len__(self) -> int:
        return len(self._metrics)
