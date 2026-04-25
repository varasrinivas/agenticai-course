"""
M20 Lab — Monitoring: Dashboard (Solution)
===========================================
Complete implementation of the terminal-based ASCII monitoring
dashboard with traffic simulator.

Usage:
    python dashboard.py
"""

import time
import random
from typing import List, Optional

from metrics_collector import MetricsCollector
from alert_engine import AlertEngine, Alert
from drift_detector import DriftDetector


# =============================================================================
# TRAFFIC SIMULATOR
# =============================================================================

def generate_traffic(
    collector: MetricsCollector,
    num_requests: int = 200,
    error_rate: float = 0.03,
    slow_pct: float = 0.10,
    very_slow_pct: float = 0.02,
) -> None:
    """Generate simulated traffic with realistic distributions."""
    tool_names = ["search_filings", "get_details", "calc_risk"]

    for _ in range(num_requests):
        # Duration distribution: most fast, some slow, few very slow
        roll = random.random()
        if roll < very_slow_pct:
            duration = random.uniform(5000, 15000)
        elif roll < very_slow_pct + slow_pct:
            duration = random.uniform(1000, 5000)
        else:
            duration = random.uniform(80, 600)

        success = random.random() >= error_rate

        input_tokens = random.randint(400, 2500)
        output_tokens = random.randint(150, 1800)

        num_tools = random.randint(1, 3)
        tools = []
        for _ in range(num_tools):
            tools.append({
                "name": random.choice(tool_names),
                "duration_ms": random.uniform(5, 120),
                "success": random.random() > 0.03,
            })

        collector.record_request(duration, input_tokens, output_tokens, success, tools)


# =============================================================================
# DASHBOARD RENDERER
# =============================================================================

class Dashboard:
    """ASCII terminal dashboard for agent monitoring."""

    WIDTH = 62  # Total width including border characters

    def __init__(
        self,
        metrics_collector: MetricsCollector,
        alert_engine: AlertEngine,
        drift_detector: DriftDetector,
    ):
        self.collector = metrics_collector
        self.alerts = alert_engine
        self.drift = drift_detector

    def render(self) -> str:
        """Render the dashboard as a string and print it."""
        metrics = self.collector.to_dict()
        alerts = self.alerts.evaluate(metrics)
        drifts = (
            self.drift.get_significant_drifts(metrics)
            if self.drift.has_baseline()
            else []
        )

        lines: List[str] = []
        inner = self.WIDTH - 4  # Space between "║ " and " ║"

        def top():
            lines.append("╔" + "═" * (self.WIDTH - 2) + "╗")

        def bottom():
            lines.append("╚" + "═" * (self.WIDTH - 2) + "╝")

        def separator():
            lines.append("╠" + "═" * (self.WIDTH - 2) + "╣")

        def row(text: str):
            # Pad or truncate text to fit
            display = text[:inner]
            lines.append("║ " + display.ljust(inner) + " ║")

        def section_header(text: str):
            separator()
            row(text)

        # === Title ===
        top()
        title = "UCC Agent Monitoring Dashboard"
        row(title.center(inner))

        # === Summary ===
        separator()
        uptime_str = self._format_uptime(metrics.get("uptime_seconds", 0))
        req_count = metrics.get("request_count", 0)
        err_rate = metrics.get("error_rate", 0)
        summary = f"Requests: {req_count:,}    Error Rate: {err_rate:.1f}%    Uptime: {uptime_str}"
        row(summary)

        # === Latency ===
        section_header("Latency (ms)")
        lat = metrics.get("latency", {})
        lat_line = (
            f"  p50: {lat.get('p50', 0):,.0f}  "
            f"p75: {lat.get('p75', 0):,.0f}  "
            f"p90: {lat.get('p90', 0):,.0f}  "
            f"p95: {lat.get('p95', 0):,.0f}  "
            f"p99: {lat.get('p99', 0):,.0f}"
        )
        row(lat_line)

        # === Cost ===
        section_header("Cost")
        tokens = metrics.get("tokens", {})
        total_cost = tokens.get("cost_estimate", 0)
        cost_hr = tokens.get("cost_per_hour", 0)
        avg_cost = total_cost / req_count if req_count > 0 else 0
        cost_line = (
            f"  Total: ${total_cost:.2f}    "
            f"Rate: ${cost_hr:.2f}/hr    "
            f"Avg: ${avg_cost:.4f}/req"
        )
        row(cost_line)

        # === Tokens ===
        section_header("Tokens")
        total_in = tokens.get("total_input", 0)
        total_out = tokens.get("total_output", 0)
        row(f"  Input: {total_in:,}    Output: {total_out:,}")

        # === Tools ===
        section_header("Tools")
        tool_stats = metrics.get("tools", {})
        if tool_stats:
            for name, stats in sorted(tool_stats.items()):
                calls = int(stats.get("calls", 0))
                fail_rate = stats.get("failure_rate", 0)
                avg_dur = stats.get("avg_duration_ms", 0)
                tool_line = f"  {name}:  {calls} calls, {fail_rate:.1f}% fail, avg {avg_dur:.0f}ms"
                row(tool_line)
        else:
            row("  No tool data")

        # === Alerts ===
        section_header("Alerts")
        if alerts:
            for alert in alerts:
                icon = {"critical": "🔴", "warning": "🟡", "info": "🔵"}.get(alert.severity, "⚪")
                alert_line = f"  {icon} [{alert.severity.upper()}] {alert.message}"
                row(alert_line)
        else:
            row("  ✅ No active alerts")

        # === Drift ===
        section_header("Drift")
        if drifts:
            for d in drifts:
                direction = "↑" if d.change_pct > 0 else "↓"
                drift_line = (
                    f"  {direction} {d.metric_name}: "
                    f"{d.baseline_value:.1f} -> {d.current_value:.1f} "
                    f"({d.change_pct:+.1f}%)"
                )
                row(drift_line)
        else:
            row("  ✅ No significant drift detected")

        bottom()

        output = "\n".join(lines)
        print(output)
        return output

    def _format_uptime(self, seconds: float) -> str:
        """Format seconds into human-readable uptime string."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        if hours > 0:
            return f"{hours}h {minutes}m"
        else:
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"


# =============================================================================
# MAIN — FULL INTEGRATION TEST
# =============================================================================

def main():
    """Run full integration: normal traffic -> dashboard -> degraded traffic -> dashboard."""
    print("=" * 62)
    print("  M20 Monitoring Dashboard — Full Integration Demo")
    print("=" * 62)

    # Step 1: Create components
    collector = MetricsCollector()
    alert_engine = AlertEngine()
    drift_detector = DriftDetector()
    dashboard = Dashboard(collector, alert_engine, drift_detector)

    # Step 2: Generate normal traffic
    print("\nGenerating 200 normal requests...")
    random.seed(42)  # Reproducible output
    generate_traffic(
        collector,
        num_requests=200,
        error_rate=0.03,
        slow_pct=0.10,
        very_slow_pct=0.02,
    )

    # Step 3: Set baseline
    drift_detector.set_baseline(collector.to_dict())

    # Step 4: Render normal dashboard
    print("\n>>> DASHBOARD — Normal Traffic")
    dashboard.render()

    # Step 5: Generate degraded traffic
    print("\n\nGenerating 50 degraded requests (25% errors, 40% slow)...")
    generate_traffic(
        collector,
        num_requests=50,
        error_rate=0.25,
        slow_pct=0.40,
        very_slow_pct=0.15,
    )

    # Step 6: Render degraded dashboard
    print("\n>>> DASHBOARD — After Degradation")
    dashboard.render()


if __name__ == "__main__":
    main()
