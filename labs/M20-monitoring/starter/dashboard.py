"""
M20 Lab — Monitoring: Dashboard (Starter)
==========================================
Build a terminal-based ASCII monitoring dashboard that ties together
the metrics collector, alert engine, and drift detector.

KEY CONCEPT: A dashboard is the "single pane of glass" for your
agent's health. When something goes wrong at 3am, the on-call
engineer opens the dashboard first. It must answer three questions
in under 5 seconds: (1) Is the system up? (2) Is it healthy?
(3) What changed recently?

Usage:
    python dashboard.py
"""

import time
import random
from typing import List, Optional

# Import the other modules from this lab
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
    """
    Generate simulated traffic with realistic distributions.

    Most requests are fast, some are slow, a few are very slow.
    Error rate and slowness are configurable to simulate degradation.

    Args:
        collector: MetricsCollector to record requests into
        num_requests: How many requests to simulate
        error_rate: Fraction of requests that fail (0.0 to 1.0)
        slow_pct: Fraction of requests that are slow (1-5s)
        very_slow_pct: Fraction of requests that are very slow (5-15s)
    """
    # TODO: Generate num_requests simulated requests
    #
    # For each request:
    # 1. Determine duration:
    #    - If random() < very_slow_pct: duration = random(5000, 15000)
    #    - Elif random() < slow_pct: duration = random(1000, 5000)
    #    - Else: duration = random(80, 600) (normal)
    #
    # 2. Determine success: random() >= error_rate
    #
    # 3. Generate tokens:
    #    - input_tokens = random(400, 2500)
    #    - output_tokens = random(150, 1800)
    #
    # 4. Generate 1-3 tool calls with names from:
    #    ["search_filings", "get_details", "calc_risk"]
    #    Each tool: duration 5-120ms, success = random() > 0.03
    #
    # 5. Record via collector.record_request()
    #
    # HINT: Use random.random(), random.uniform(), random.randint(), random.choice()
    pass


# =============================================================================
# DASHBOARD RENDERER
# =============================================================================

class Dashboard:
    """
    ASCII terminal dashboard for agent monitoring.

    Renders a box-drawing character dashboard showing:
    - Request count, error rate, uptime
    - Latency percentiles
    - Token cost breakdown
    - Per-tool statistics
    - Active alerts
    - Drift events
    """

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
        """
        Render the dashboard as a string and print it.

        Returns the rendered string for testing/capture.
        """
        # TODO: Build the ASCII dashboard string
        #
        # Layout (use box-drawing characters):
        # 1. Title bar
        # 2. Summary row: requests, error rate, uptime
        # 3. Latency section: p50, p75, p90, p95, p99
        # 4. Cost section: total, rate/hr, avg/request
        # 5. Tools section: per-tool stats table
        # 6. Alerts section: list of active alerts or "No active alerts"
        # 7. Drift section: list of drift events or "No significant drift"
        #
        # Use these box-drawing characters:
        #   ╔ ═ ╗   (top corners and horizontal)
        #   ║   ║   (vertical sides)
        #   ╠ ═ ╣   (middle separators)
        #   ╚ ═ ╝   (bottom corners)
        #
        # HINT: Use a fixed width (e.g., 62 characters including borders)
        # HINT: Create helper methods:
        #   _header_line(text) -> "╠══════...══════╣" with text
        #   _content_line(text) -> "║ text          ║" (padded)
        #
        # Steps:
        # 1. Get all metrics: self.collector.to_dict()
        # 2. Get alerts: self.alerts.evaluate(metrics)
        # 3. Get drift: self.drift.get_significant_drifts(metrics) if baseline exists
        # 4. Format each section
        # 5. Join with newlines, print, and return

        pass

    def _format_uptime(self, seconds: float) -> str:
        """Format seconds into human-readable uptime string."""
        # TODO: Convert seconds to "Xh Ym" or "Xm Ys" format
        # HINT: hours = int(seconds // 3600)
        #        minutes = int((seconds % 3600) // 60)
        pass


# =============================================================================
# MAIN — FULL INTEGRATION TEST
# =============================================================================

def main():
    """
    Run full integration: normal traffic -> dashboard -> degraded traffic -> dashboard.

    This demonstrates:
    1. Baseline behavior with normal traffic
    2. How alerts fire when metrics degrade
    3. How drift detection catches changes from baseline
    """
    print("=" * 62)
    print("  M20 Monitoring Dashboard — Full Integration Demo")
    print("=" * 62)

    # TODO: Implement the full integration
    #
    # Step 1: Create components
    #   collector = MetricsCollector()
    #   alert_engine = AlertEngine()
    #   drift_detector = DriftDetector()
    #   dashboard = Dashboard(collector, alert_engine, drift_detector)
    #
    # Step 2: Generate normal traffic (200 requests, 3% error, 10% slow)
    #   generate_traffic(collector, num_requests=200, error_rate=0.03, slow_pct=0.10)
    #
    # Step 3: Set baseline for drift detection
    #   drift_detector.set_baseline(collector.to_dict())
    #
    # Step 4: Render "normal" dashboard
    #   print("\n>>> DASHBOARD — Normal Traffic")
    #   dashboard.render()
    #
    # Step 5: Generate degraded traffic (50 requests, 25% error, 40% slow, 15% very slow)
    #   generate_traffic(collector, num_requests=50, error_rate=0.25, slow_pct=0.40, very_slow_pct=0.15)
    #
    # Step 6: Render "degraded" dashboard (should show alerts and drift)
    #   print("\n>>> DASHBOARD — After Degradation")
    #   dashboard.render()
    pass


if __name__ == "__main__":
    main()
