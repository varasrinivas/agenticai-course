"""
M20 Lab — Monitoring: Alert Engine (Solution)
==============================================
Complete implementation of the alert engine with default rules
for error rate, latency, cost, tool failures, and staleness.

Usage:
    python alert_engine.py
"""

import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Any, Optional


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class AlertRule:
    """A rule that defines when an alert should fire."""
    name: str
    condition_fn: Callable[[Dict], bool]
    severity: str  # "critical" | "warning" | "info"
    message_template: str
    value_fn: Optional[Callable[[Dict], Any]] = None


@dataclass
class Alert:
    """A triggered alert."""
    rule_name: str
    severity: str
    message: str
    timestamp: float
    metric_value: Any


# =============================================================================
# ALERT ENGINE
# =============================================================================

class AlertEngine:
    """
    Evaluates metrics against registered rules and produces alerts.
    """

    def __init__(self):
        self.rules: List[AlertRule] = []
        self._setup_default_rules()

    def _setup_default_rules(self) -> None:
        """Register the default set of alert rules."""

        # Rule 1: High error rate (>5% = critical)
        self.add_rule(AlertRule(
            name="high_error_rate",
            condition_fn=lambda m: m.get("error_rate", 0) > 5,
            severity="critical",
            message_template="Error rate is {value:.1f}% (threshold: 5%)",
            value_fn=lambda m: m.get("error_rate", 0),
        ))

        # Rule 2: High latency p95 (>10,000ms = warning)
        self.add_rule(AlertRule(
            name="high_latency_p95",
            condition_fn=lambda m: m.get("latency", {}).get("p95", 0) > 10000,
            severity="warning",
            message_template="P95 latency is {value:.0f}ms (threshold: 10,000ms)",
            value_fn=lambda m: m.get("latency", {}).get("p95", 0),
        ))

        # Rule 3: High cost (>$1/hr = warning)
        self.add_rule(AlertRule(
            name="high_cost",
            condition_fn=lambda m: m.get("tokens", {}).get("cost_per_hour", 0) > 1.0,
            severity="warning",
            message_template="Cost rate is ${value:.2f}/hr (threshold: $1.00/hr)",
            value_fn=lambda m: m.get("tokens", {}).get("cost_per_hour", 0),
        ))

        # Rule 4: Tool failure rate (any tool >10% = critical)
        def check_tool_failure(m):
            tools = m.get("tools", {})
            for tool_name, stats in tools.items():
                if stats.get("failure_rate", 0) > 10:
                    return True
            return False

        def get_max_tool_failure(m):
            tools = m.get("tools", {})
            max_rate = 0
            for tool_name, stats in tools.items():
                rate = stats.get("failure_rate", 0)
                if rate > max_rate:
                    max_rate = rate
            return max_rate

        self.add_rule(AlertRule(
            name="tool_failure_rate",
            condition_fn=check_tool_failure,
            severity="critical",
            message_template="Tool failure rate is {value:.1f}% (threshold: 10%)",
            value_fn=get_max_tool_failure,
        ))

        # Rule 5: Stale — no requests for 5+ minutes
        self.add_rule(AlertRule(
            name="stale_no_requests",
            condition_fn=lambda m: (
                m.get("throughput_rpm", 0) == 0
                and m.get("uptime_seconds", 0) > 300
            ),
            severity="info",
            message_template="No requests in last 5 minutes (uptime: {value:.0f}s)",
            value_fn=lambda m: m.get("uptime_seconds", 0),
        ))

    def add_rule(self, rule: AlertRule) -> None:
        """Register a new alert rule."""
        self.rules.append(rule)

    def evaluate(self, metrics: Dict) -> List[Alert]:
        """Evaluate all rules against the given metrics."""
        triggered: List[Alert] = []

        for rule in self.rules:
            try:
                if rule.condition_fn(metrics):
                    value = rule.value_fn(metrics) if rule.value_fn else None
                    message = rule.message_template.format(value=value) if value is not None else rule.message_template
                    triggered.append(Alert(
                        rule_name=rule.name,
                        severity=rule.severity,
                        message=message,
                        timestamp=time.time(),
                        metric_value=value,
                    ))
            except Exception as e:
                # Don't let one bad rule stop evaluation of others
                pass

        return triggered


# =============================================================================
# SELF-TEST
# =============================================================================

def self_test():
    """Test alert engine with metrics that trigger various alerts."""
    print("=" * 60)
    print("M20 Alert Engine — Self-Test")
    print("=" * 60)

    engine = AlertEngine()

    # --- Test 1: Healthy metrics ---
    healthy_metrics = {
        "request_count": 500,
        "error_rate": 1.2,
        "latency": {"p50": 200, "p75": 400, "p90": 800, "p95": 1500, "p99": 3000},
        "tokens": {
            "total_input": 500000,
            "total_output": 250000,
            "cost_estimate": 0.50,
            "cost_per_hour": 0.25,
        },
        "tools": {
            "search_filings": {"calls": 300, "failures": 5, "failure_rate": 1.7, "avg_duration_ms": 45},
            "get_details": {"calls": 200, "failures": 2, "failure_rate": 1.0, "avg_duration_ms": 12},
        },
        "throughput_rpm": 8.3,
        "uptime_seconds": 3600,
    }

    alerts = engine.evaluate(healthy_metrics)
    print(f"\nHealthy metrics -> {len(alerts)} alerts")
    assert len(alerts) == 0, f"Expected 0 alerts for healthy metrics, got {len(alerts)}"
    print("  ✅ No alerts — PASS")

    # --- Test 2: Degraded metrics ---
    degraded_metrics = {
        "request_count": 500,
        "error_rate": 8.5,
        "latency": {"p50": 2000, "p75": 5000, "p90": 9000, "p95": 12000, "p99": 18000},
        "tokens": {
            "total_input": 5000000,
            "total_output": 2500000,
            "cost_estimate": 52.50,
            "cost_per_hour": 2.10,
        },
        "tools": {
            "search_filings": {"calls": 300, "failures": 45, "failure_rate": 15.0, "avg_duration_ms": 145},
            "get_details": {"calls": 200, "failures": 2, "failure_rate": 1.0, "avg_duration_ms": 12},
        },
        "throughput_rpm": 8.3,
        "uptime_seconds": 3600,
    }

    alerts = engine.evaluate(degraded_metrics)
    print(f"\nDegraded metrics -> {len(alerts)} alerts")
    for alert in alerts:
        severity_icon = {"critical": "🔴", "warning": "🟡", "info": "🔵"}[alert.severity]
        print(f"  {severity_icon} [{alert.severity.upper()}] {alert.rule_name}: {alert.message}")

    assert len(alerts) >= 3, f"Expected at least 3 alerts, got {len(alerts)}"
    severities = [a.severity for a in alerts]
    assert "critical" in severities, "Expected at least one critical alert"
    print("  ✅ Multiple alerts with correct severities — PASS")

    # --- Test 3: Stale metrics ---
    stale_metrics = {
        "request_count": 0,
        "error_rate": 0,
        "latency": {"p50": 0, "p75": 0, "p90": 0, "p95": 0, "p99": 0},
        "tokens": {
            "total_input": 0,
            "total_output": 0,
            "cost_estimate": 0,
            "cost_per_hour": 0,
        },
        "tools": {},
        "throughput_rpm": 0,
        "uptime_seconds": 600,
    }

    alerts = engine.evaluate(stale_metrics)
    print(f"\nStale metrics -> {len(alerts)} alerts")
    for alert in alerts:
        severity_icon = {"critical": "🔴", "warning": "🟡", "info": "🔵"}[alert.severity]
        print(f"  {severity_icon} [{alert.severity.upper()}] {alert.rule_name}: {alert.message}")

    stale_alerts = [a for a in alerts if a.rule_name == "stale_no_requests"]
    assert len(stale_alerts) >= 1, "Expected stale alert"
    print("  ✅ Stale detection works — PASS")

    print(f"\n{'=' * 60}")
    print("Self-test complete!")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    self_test()
