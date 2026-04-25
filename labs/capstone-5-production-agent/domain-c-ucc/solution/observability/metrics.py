"""
Metrics Collector — cost, latency, and token usage tracking.
(Solution — fully implemented)
"""

import time
import statistics
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime


@dataclass
class RequestMetric:
    request_id: str
    task_type: str
    model_tier: str
    model_id: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_usd: float
    latency_ms: float
    status: str
    timestamp: str
    tool_calls: int = 0
    agent_handoffs: int = 0


class MetricsCollector:
    """Collects and reports on system metrics."""

    def __init__(self):
        self._metrics: List[RequestMetric] = []
        self._cost_by_tier: Dict[str, float] = {"fast": 0.0, "balanced": 0.0, "powerful": 0.0}
        self._tokens_by_tier: Dict[str, Dict[str, int]] = {
            "fast": {"input": 0, "output": 0},
            "balanced": {"input": 0, "output": 0},
            "powerful": {"input": 0, "output": 0},
        }

    def record(
        self, request_id: str, task_type: str, model_tier: str,
        model_id: str, input_tokens: int, output_tokens: int,
        cost_usd: float, latency_ms: float, status: str = "success",
        tool_calls: int = 0, agent_handoffs: int = 0,
    ) -> None:
        metric = RequestMetric(
            request_id=request_id, task_type=task_type, model_tier=model_tier,
            model_id=model_id, input_tokens=input_tokens, output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens, cost_usd=cost_usd,
            latency_ms=latency_ms, status=status,
            timestamp=datetime.utcnow().isoformat(),
            tool_calls=tool_calls, agent_handoffs=agent_handoffs,
        )
        self._metrics.append(metric)

        if model_tier in self._cost_by_tier:
            self._cost_by_tier[model_tier] += cost_usd
        if model_tier in self._tokens_by_tier:
            self._tokens_by_tier[model_tier]["input"] += input_tokens
            self._tokens_by_tier[model_tier]["output"] += output_tokens

    def get_cost_report(self) -> Dict[str, Any]:
        total = sum(self._cost_by_tier.values())
        count = len(self._metrics)
        most_expensive = max(self._cost_by_tier, key=self._cost_by_tier.get) if self._cost_by_tier else None
        return {
            "total_cost_usd": round(total, 6),
            "cost_by_tier": {k: round(v, 6) for k, v in self._cost_by_tier.items()},
            "cost_per_request_avg": round(total / count, 6) if count > 0 else 0.0,
            "most_expensive_tier": most_expensive,
            "request_count": count,
        }

    def get_latency_percentiles(self, task_type: Optional[str] = None) -> Dict[str, float]:
        latencies = [m.latency_ms for m in self._metrics
                     if task_type is None or m.task_type == task_type]
        if not latencies:
            return {"p50": 0.0, "p95": 0.0, "p99": 0.0, "mean": 0.0, "min": 0.0, "max": 0.0}

        latencies.sort()
        n = len(latencies)
        if n == 1:
            v = latencies[0]
            return {"p50": v, "p95": v, "p99": v, "mean": v, "min": v, "max": v}

        def percentile(data, p):
            k = (len(data) - 1) * p / 100
            f = int(k)
            c = f + 1
            if c >= len(data):
                return data[-1]
            return data[f] + (k - f) * (data[c] - data[f])

        return {
            "p50": round(percentile(latencies, 50), 2),
            "p95": round(percentile(latencies, 95), 2),
            "p99": round(percentile(latencies, 99), 2),
            "mean": round(statistics.mean(latencies), 2),
            "min": round(min(latencies), 2),
            "max": round(max(latencies), 2),
        }

    def get_token_usage(self) -> Dict[str, Any]:
        total_in = sum(t["input"] for t in self._tokens_by_tier.values())
        total_out = sum(t["output"] for t in self._tokens_by_tier.values())
        count = len(self._metrics)
        tokens_by_tier = {}
        for tier, data in self._tokens_by_tier.items():
            tokens_by_tier[tier] = {
                "input": data["input"], "output": data["output"],
                "total": data["input"] + data["output"],
            }
        return {
            "total_input_tokens": total_in,
            "total_output_tokens": total_out,
            "total_tokens": total_in + total_out,
            "tokens_by_tier": tokens_by_tier,
            "avg_tokens_per_request": round((total_in + total_out) / count, 1) if count > 0 else 0,
        }

    def get_request_stats(self) -> Dict[str, Any]:
        count = len(self._metrics)
        by_type = {}
        by_status = {"success": 0, "error": 0}
        total_tool_calls = 0
        for m in self._metrics:
            by_type[m.task_type] = by_type.get(m.task_type, 0) + 1
            by_status[m.status] = by_status.get(m.status, 0) + 1
            total_tool_calls += m.tool_calls
        return {
            "total_requests": count,
            "requests_by_type": by_type,
            "requests_by_status": by_status,
            "success_rate": round(by_status["success"] / count, 4) if count > 0 else 0.0,
            "avg_tool_calls_per_request": round(total_tool_calls / count, 2) if count > 0 else 0.0,
        }

    def format_dashboard(self) -> str:
        if not self._metrics:
            return (
                "+-------------------------------------------------+\n"
                "|       UCC PRODUCTION AGENT DASHBOARD             |\n"
                "+-------------------------------------------------+\n"
                "|  No requests recorded yet.                       |\n"
                "+-------------------------------------------------+"
            )

        cost = self.get_cost_report()
        latency = self.get_latency_percentiles()
        tokens = self.get_token_usage()
        stats = self.get_request_stats()

        w = 55
        sep = "+" + "-" * (w - 2) + "+"

        lines = [sep]
        lines.append("|" + "UCC PRODUCTION AGENT DASHBOARD".center(w - 2) + "|")
        lines.append(sep)

        sr = stats["success_rate"] * 100
        lines.append("|" + f"  Requests: {stats['total_requests']}  |  Success Rate: {sr:.1f}%".ljust(w - 2) + "|")
        avg_cost = cost['cost_per_request_avg']
        lines.append("|" + f"  Total Cost: ${cost['total_cost_usd']:.4f}  |  Avg: ${avg_cost:.4f}/req".ljust(w - 2) + "|")
        lines.append(sep)

        lines.append("|" + "  Cost by Tier:".ljust(w - 2) + "|")
        for tier in ["fast", "balanced", "powerful"]:
            tier_cost = cost["cost_by_tier"].get(tier, 0)
            tier_reqs = sum(1 for m in self._metrics if m.model_tier == tier)
            lines.append("|" + f"    {tier:10s} ${tier_cost:.4f}  ({tier_reqs} requests)".ljust(w - 2) + "|")
        lines.append(sep)

        lines.append("|" + "  Latency:".ljust(w - 2) + "|")
        lines.append("|" + f"    p50: {latency['p50']:.0f}ms  p95: {latency['p95']:.0f}ms  p99: {latency['p99']:.0f}ms".ljust(w - 2) + "|")
        lines.append(sep)

        lines.append("|" + "  Tokens:".ljust(w - 2) + "|")
        lines.append("|" + f"    Total: {tokens['total_tokens']:,}  (in: {tokens['total_input_tokens']:,}  out: {tokens['total_output_tokens']:,})".ljust(w - 2) + "|")
        lines.append("|" + f"    Avg/request: {tokens['avg_tokens_per_request']:,.0f}".ljust(w - 2) + "|")
        lines.append(sep)

        return "\n".join(lines)

    def __len__(self) -> int:
        return len(self._metrics)
