"""
M20 Lab — Monitoring: Drift Detector (Starter)
===============================================
Build a drift detector that compares current metrics against a
saved baseline and flags significant changes.

KEY CONCEPT: Threshold alerts catch sudden spikes — error rate
jumps from 2% to 15%, the pager goes off. But what about slow
degradation? If latency creeps up 3% per day, no single day
triggers an alert, but after two weeks your p95 has doubled.
Drift detection catches this by comparing current metrics to a
known-good baseline and flagging anything that has changed
significantly (default: >20%).

Usage:
    python drift_detector.py
"""

import time
import copy
from dataclasses import dataclass
from typing import Dict, List, Optional, Any


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class DriftEvent:
    """
    A detected drift in a single metric.

    Attributes:
        metric_name: Which metric drifted (e.g., "latency_p95")
        baseline_value: The value from the baseline snapshot
        current_value: The current value
        change_pct: Percentage change from baseline (can be negative)
        is_significant: Whether the change exceeds the significance threshold
    """
    metric_name: str
    baseline_value: float
    current_value: float
    change_pct: float
    is_significant: bool


# =============================================================================
# DRIFT DETECTOR
# =============================================================================

class DriftDetector:
    """
    Detects metric drift by comparing current values against a baseline.

    Monitors these metrics for drift:
    - error_rate
    - latency_p50, latency_p75, latency_p90, latency_p95, latency_p99
    - token cost_per_hour
    - throughput_rpm
    - per-tool failure rates
    """

    def __init__(self, significance_threshold: float = 20.0):
        """
        Args:
            significance_threshold: Percentage change that counts as significant.
                                    Default 20.0 means >20% change triggers drift.
        """
        self.significance_threshold = significance_threshold
        self.baseline: Optional[Dict] = None
        self.baseline_timestamp: Optional[float] = None

    def set_baseline(self, metrics: Dict) -> None:
        """
        Store a metrics snapshot as the baseline for future comparisons.

        Args:
            metrics: Dict from MetricsCollector.to_dict()
        """
        # TODO: Deep copy the metrics dict and store it
        # HINT: Use copy.deepcopy() to prevent the baseline from changing
        #   when the original dict is modified
        # HINT: Also store time.time() as baseline_timestamp
        pass

    def detect_drift(self, current_metrics: Dict) -> List[DriftEvent]:
        """
        Compare current metrics against the baseline and return drift events.

        Args:
            current_metrics: Dict from MetricsCollector.to_dict()

        Returns:
            List of DriftEvent objects for all compared metrics
            (both significant and non-significant)
        """
        # TODO: Implement drift detection
        # If no baseline is set, return empty list
        #
        # Compare these metrics:
        # 1. "error_rate" — direct comparison
        # 2. Latency percentiles — compare each of p50, p75, p90, p95, p99
        #    from current_metrics["latency"] vs self.baseline["latency"]
        # 3. "cost_per_hour" — from current_metrics["tokens"]["cost_per_hour"]
        # 4. "throughput_rpm" — direct comparison
        # 5. Per-tool failure rates — for each tool in both baseline and current
        #
        # For each metric:
        #   - Calculate change_pct = ((current - baseline) / baseline) * 100
        #   - Handle baseline == 0: if current > 0, change is significant;
        #     if both 0, change_pct is 0
        #   - is_significant = abs(change_pct) > self.significance_threshold
        #   - Create a DriftEvent
        #
        # HINT: Use a helper method _compare_values(name, baseline_val, current_val)
        #   that returns a DriftEvent
        pass

    def _compare_values(
        self, name: str, baseline_val: float, current_val: float
    ) -> DriftEvent:
        """
        Compare two values and return a DriftEvent.

        Handles edge case where baseline is 0.
        """
        # TODO: Calculate change_pct and is_significant
        # HINT: If baseline_val == 0 and current_val > 0, treat as significant
        #   with change_pct = 100.0
        # HINT: If both are 0, change_pct = 0, not significant
        # HINT: Otherwise change_pct = ((current - baseline) / baseline) * 100
        pass

    def get_significant_drifts(self, current_metrics: Dict) -> List[DriftEvent]:
        """Return only the significant drift events."""
        # TODO: Filter detect_drift() results to only is_significant == True
        pass

    def has_baseline(self) -> bool:
        """Check if a baseline has been set."""
        return self.baseline is not None


# =============================================================================
# DRIFT SIMULATION HELPER
# =============================================================================

def simulate_drift(metrics: Dict, degradation_factor: float = 1.5) -> Dict:
    """
    Artificially degrade metrics to test drift detection.

    Args:
        metrics: Original metrics dict
        degradation_factor: How much to degrade (1.5 = 50% worse)

    Returns:
        New metrics dict with degraded values
    """
    # TODO: Create a deep copy of metrics and degrade key values
    # - Multiply error_rate by degradation_factor
    # - Multiply all latency percentiles by degradation_factor
    # - Multiply cost_per_hour by degradation_factor
    # - Reduce throughput_rpm by dividing by degradation_factor
    # - Increase tool failure rates by degradation_factor
    #
    # HINT: Use copy.deepcopy() so you don't modify the original
    pass


# =============================================================================
# SELF-TEST
# =============================================================================

def self_test():
    """Test drift detection with baseline and degraded metrics."""
    print("=" * 60)
    print("M20 Drift Detector — Self-Test")
    print("=" * 60)

    detector = DriftDetector(significance_threshold=20.0)

    # Baseline metrics (healthy)
    baseline = {
        "request_count": 500,
        "error_rate": 2.0,
        "latency": {"p50": 200, "p75": 400, "p90": 800, "p95": 1500, "p99": 3000},
        "tokens": {
            "total_input": 500000,
            "total_output": 250000,
            "cost_estimate": 5.25,
            "cost_per_hour": 0.50,
        },
        "tools": {
            "search_filings": {"calls": 300, "failures": 5, "failure_rate": 1.7, "avg_duration_ms": 45},
            "get_details": {"calls": 200, "failures": 2, "failure_rate": 1.0, "avg_duration_ms": 12},
        },
        "throughput_rpm": 8.3,
        "uptime_seconds": 3600,
    }

    detector.set_baseline(baseline)
    print(f"\nBaseline set at {time.strftime('%H:%M:%S')}")

    # --- Test 1: No drift (same metrics) ---
    drifts = detector.get_significant_drifts(baseline)
    print(f"\nSame metrics -> {len(drifts)} significant drifts")
    assert len(drifts) == 0, "Expected no drift when metrics match baseline"
    print("  ✅ No drift with identical metrics — PASS")

    # --- Test 2: Simulated degradation ---
    degraded = simulate_drift(baseline, degradation_factor=1.5)
    all_drifts = detector.detect_drift(degraded)
    significant = [d for d in all_drifts if d.is_significant]

    print(f"\nDegraded metrics (1.5x) -> {len(significant)} significant drifts out of {len(all_drifts)} total")
    for drift in significant:
        direction = "↑" if drift.change_pct > 0 else "↓"
        print(f"  {direction} {drift.metric_name}: "
              f"{drift.baseline_value:.1f} → {drift.current_value:.1f} "
              f"({drift.change_pct:+.1f}%)")

    assert len(significant) >= 2, f"Expected at least 2 significant drifts, got {len(significant)}"
    print("  ✅ Drift detected after degradation — PASS")

    # --- Test 3: Minor change (below threshold) ---
    minor_change = copy.deepcopy(baseline)
    minor_change["error_rate"] = 2.2  # 10% increase, below 20% threshold
    drifts = detector.get_significant_drifts(minor_change)
    error_drifts = [d for d in drifts if d.metric_name == "error_rate"]
    assert len(error_drifts) == 0, "10% change should not be significant at 20% threshold"
    print(f"\n  ✅ Minor change (10%) correctly ignored — PASS")

    print(f"\n{'=' * 60}")
    print("Self-test complete!")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    self_test()
