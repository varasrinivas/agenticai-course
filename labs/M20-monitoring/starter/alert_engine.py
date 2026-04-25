"""
M20 Lab — Monitoring: Alert Engine (Starter)
=============================================
Build an alert engine that evaluates metrics against configurable
rules and fires alerts when thresholds are breached.

KEY CONCEPT: Alerts are the bridge between metrics and action.
Without alerts, dashboards are just screensavers — pretty to look
at but nobody's watching. A good alert engine has severity levels
(critical vs warning vs info) so on-call engineers know what
needs immediate attention vs what can wait until morning.

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
    """
    A rule that defines when an alert should fire.

    Attributes:
        name: Human-readable rule name (e.g., "high_error_rate")
        condition_fn: Function that takes metrics dict, returns True if alert should fire
        severity: "critical", "warning", or "info"
        message_template: Format string with {value} placeholder
    """
    name: str
    condition_fn: Callable[[Dict], bool]
    severity: str  # "critical" | "warning" | "info"
    message_template: str


@dataclass
class Alert:
    """
    A triggered alert.

    Attributes:
        rule_name: Which rule triggered this alert
        severity: Inherited from the rule
        message: Formatted message with actual metric value
        timestamp: When the alert was triggered
        metric_value: The actual value that triggered the alert
    """
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

    Default rules:
    - Error rate > 5% --> critical
    - Latency p95 > 10,000ms --> warning
    - Cost > $1/hour --> warning
    - Any tool failure rate > 10% --> critical
    - No requests for 5+ minutes --> info (stale)
    """

    def __init__(self):
        self.rules: List[AlertRule] = []
        self._setup_default_rules()

    def _setup_default_rules(self) -> None:
        """Register the default set of alert rules."""
        # TODO: Add 5 default rules using self.add_rule()
        #
        # Rule 1: High error rate
        # - Name: "high_error_rate"
        # - Condition: metrics["error_rate"] > 5
        # - Severity: "critical"
        # - Message: "Error rate is {value:.1f}% (threshold: 5%)"
        #
        # Rule 2: High latency
        # - Name: "high_latency_p95"
        # - Condition: metrics["latency"]["p95"] > 10000
        # - Severity: "warning"
        # - Message: "P95 latency is {value:.0f}ms (threshold: 10,000ms)"
        #
        # Rule 3: High cost
        # - Name: "high_cost"
        # - Condition: metrics["tokens"]["cost_per_hour"] > 1.0
        # - Severity: "warning"
        # - Message: "Cost rate is ${value:.2f}/hr (threshold: $1.00/hr)"
        #
        # Rule 4: Tool failure rate
        # - Name: "tool_failure_rate"
        # - Condition: any tool in metrics["tools"] has failure_rate > 10
        # - Severity: "critical"
        # - Message: "Tool failure rate is {value:.1f}% (threshold: 10%)"
        #
        # Rule 5: Stale (no recent requests)
        # - Name: "stale_no_requests"
        # - Condition: metrics["throughput_rpm"] == 0 and metrics["uptime_seconds"] > 300
        # - Severity: "info"
        # - Message: "No requests in last 5 minutes (uptime: {value:.0f}s)"
        #
        # HINT: Each condition_fn should handle KeyError gracefully (return False)
        # HINT: Use try/except in condition functions for robustness
        pass

    def add_rule(self, rule: AlertRule) -> None:
        """Register a new alert rule."""
        # TODO: Append the rule to self.rules
        pass

    def evaluate(self, metrics: Dict) -> List[Alert]:
        """
        Evaluate all rules against the given metrics.

        Args:
            metrics: Dict from MetricsCollector.to_dict()

        Returns:
            List of Alert objects for all triggered rules
        """
        # TODO: Iterate through self.rules
        # For each rule:
        #   1. Call rule.condition_fn(metrics) — if True, the rule triggered
        #   2. Extract the relevant metric value for the message
        #   3. Format rule.message_template with the value
        #   4. Create an Alert object
        #   5. Collect all triggered alerts and return them
        #
        # HINT: Wrap each rule evaluation in try/except to prevent one bad rule
        #   from stopping evaluation of other rules
        # HINT: For extracting metric values, you'll need to know which metric
        #   each rule checks — consider storing a value_fn on the rule or
        #   extracting it inside the condition check
        pass


# =============================================================================
# SELF-TEST
# =============================================================================

def self_test():
    """Test alert engine with metrics that trigger various alerts."""
    print("=" * 60)
    print("M20 Alert Engine — Self-Test")
    print("=" * 60)

    engine = AlertEngine()

    # --- Test 1: Healthy metrics (no alerts) ---
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

    # --- Test 2: Degraded metrics (should trigger alerts) ---
    degraded_metrics = {
        "request_count": 500,
        "error_rate": 8.5,  # > 5% threshold
        "latency": {"p50": 2000, "p75": 5000, "p90": 9000, "p95": 12000, "p99": 18000},  # p95 > 10s
        "tokens": {
            "total_input": 5000000,
            "total_output": 2500000,
            "cost_estimate": 52.50,
            "cost_per_hour": 2.10,  # > $1/hr
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

    assert len(alerts) >= 3, f"Expected at least 3 alerts for degraded metrics, got {len(alerts)}"
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
        "uptime_seconds": 600,  # 10 minutes, no requests
    }

    alerts = engine.evaluate(stale_metrics)
    print(f"\nStale metrics -> {len(alerts)} alerts")
    for alert in alerts:
        severity_icon = {"critical": "🔴", "warning": "🟡", "info": "🔵"}[alert.severity]
        print(f"  {severity_icon} [{alert.severity.upper()}] {alert.rule_name}: {alert.message}")

    stale_alerts = [a for a in alerts if a.rule_name == "stale_no_requests"]
    assert len(stale_alerts) >= 1, "Expected stale alert when no requests for 10 minutes"
    print("  ✅ Stale detection works — PASS")

    print(f"\n{'=' * 60}")
    print("Self-test complete!")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    self_test()
