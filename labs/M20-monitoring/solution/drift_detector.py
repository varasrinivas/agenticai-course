"""
M20 Lab — Monitoring: Drift Detector (Solution)
================================================
Complete implementation of drift detection comparing current
metrics against a saved baseline.

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
    """A detected drift in a single metric."""
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
    """

    def __init__(self, significance_threshold: float = 20.0):
        self.significance_threshold = significance_threshold
        self.baseline: Optional[Dict] = None
        self.baseline_timestamp: Optional[float] = None

    def set_baseline(self, metrics: Dict) -> None:
        """Store a metrics snapshot as the baseline."""
        self.baseline = copy.deepcopy(metrics)
        self.baseline_timestamp = time.time()

    def detect_drift(self, current_metrics: Dict) -> List[DriftEvent]:
        """Compare current metrics against the baseline and return drift events."""
        if self.baseline is None:
            return []

        events: List[DriftEvent] = []

        # 1. Error rate
        events.append(self._compare_values(
            "error_rate",
            self.baseline.get("error_rate", 0),
            current_metrics.get("error_rate", 0),
        ))

        # 2. Latency percentiles
        baseline_lat = self.baseline.get("latency", {})
        current_lat = current_metrics.get("latency", {})
        for p in ["p50", "p75", "p90", "p95", "p99"]:
            events.append(self._compare_values(
                f"latency_{p}",
                baseline_lat.get(p, 0),
                current_lat.get(p, 0),
            ))

        # 3. Cost per hour
        events.append(self._compare_values(
            "cost_per_hour",
            self.baseline.get("tokens", {}).get("cost_per_hour", 0),
            current_metrics.get("tokens", {}).get("cost_per_hour", 0),
        ))

        # 4. Throughput
        events.append(self._compare_values(
            "throughput_rpm",
            self.baseline.get("throughput_rpm", 0),
            current_metrics.get("throughput_rpm", 0),
        ))

        # 5. Per-tool failure rates
        baseline_tools = self.baseline.get("tools", {})
        current_tools = current_metrics.get("tools", {})
        all_tool_names = set(list(baseline_tools.keys()) + list(current_tools.keys()))
        for tool_name in sorted(all_tool_names):
            b_rate = baseline_tools.get(tool_name, {}).get("failure_rate", 0)
            c_rate = current_tools.get(tool_name, {}).get("failure_rate", 0)
            events.append(self._compare_values(
                f"tool_{tool_name}_failure_rate",
                b_rate,
                c_rate,
            ))

        return events

    def _compare_values(
        self, name: str, baseline_val: float, current_val: float
    ) -> DriftEvent:
        """Compare two values and return a DriftEvent."""
        if baseline_val == 0:
            if current_val > 0:
                change_pct = 100.0
                is_significant = True
            else:
                change_pct = 0.0
                is_significant = False
        else:
            change_pct = ((current_val - baseline_val) / baseline_val) * 100.0
            is_significant = abs(change_pct) > self.significance_threshold

        return DriftEvent(
            metric_name=name,
            baseline_value=baseline_val,
            current_value=current_val,
            change_pct=change_pct,
            is_significant=is_significant,
        )

    def get_significant_drifts(self, current_metrics: Dict) -> List[DriftEvent]:
        """Return only the significant drift events."""
        return [d for d in self.detect_drift(current_metrics) if d.is_significant]

    def has_baseline(self) -> bool:
        """Check if a baseline has been set."""
        return self.baseline is not None


# =============================================================================
# DRIFT SIMULATION HELPER
# =============================================================================

def simulate_drift(metrics: Dict, degradation_factor: float = 1.5) -> Dict:
    """Artificially degrade metrics to test drift detection."""
    degraded = copy.deepcopy(metrics)

    # Degrade error rate
    degraded["error_rate"] = degraded.get("error_rate", 0) * degradation_factor

    # Degrade latency
    if "latency" in degraded:
        for p in ["p50", "p75", "p90", "p95", "p99"]:
            if p in degraded["latency"]:
                degraded["latency"][p] *= degradation_factor

    # Degrade cost
    if "tokens" in degraded:
        degraded["tokens"]["cost_per_hour"] = (
            degraded["tokens"].get("cost_per_hour", 0) * degradation_factor
        )
        degraded["tokens"]["cost_estimate"] = (
            degraded["tokens"].get("cost_estimate", 0) * degradation_factor
        )

    # Reduce throughput
    degraded["throughput_rpm"] = (
        degraded.get("throughput_rpm", 0) / degradation_factor
    )

    # Increase tool failure rates
    if "tools" in degraded:
        for tool_name in degraded["tools"]:
            degraded["tools"][tool_name]["failure_rate"] = (
                degraded["tools"][tool_name].get("failure_rate", 0) * degradation_factor
            )

    return degraded


# =============================================================================
# SELF-TEST
# =============================================================================

def self_test():
    """Test drift detection with baseline and degraded metrics."""
    print("=" * 60)
    print("M20 Drift Detector — Self-Test")
    print("=" * 60)

    detector = DriftDetector(significance_threshold=20.0)

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

    # Test 1: No drift
    drifts = detector.get_significant_drifts(baseline)
    print(f"\nSame metrics -> {len(drifts)} significant drifts")
    assert len(drifts) == 0, "Expected no drift when metrics match baseline"
    print("  ✅ No drift with identical metrics — PASS")

    # Test 2: Simulated degradation
    degraded = simulate_drift(baseline, degradation_factor=1.5)
    all_drifts = detector.detect_drift(degraded)
    significant = [d for d in all_drifts if d.is_significant]

    print(f"\nDegraded metrics (1.5x) -> {len(significant)} significant drifts out of {len(all_drifts)} total")
    for drift in significant:
        direction = "↑" if drift.change_pct > 0 else "↓"
        print(f"  {direction} {drift.metric_name}: "
              f"{drift.baseline_value:.1f} -> {drift.current_value:.1f} "
              f"({drift.change_pct:+.1f}%)")

    assert len(significant) >= 2, f"Expected at least 2 significant drifts, got {len(significant)}"
    print("  ✅ Drift detected after degradation — PASS")

    # Test 3: Minor change
    minor_change = copy.deepcopy(baseline)
    minor_change["error_rate"] = 2.2
    drifts = detector.get_significant_drifts(minor_change)
    error_drifts = [d for d in drifts if d.metric_name == "error_rate"]
    assert len(error_drifts) == 0, "10% change should not be significant at 20% threshold"
    print(f"\n  ✅ Minor change (10%) correctly ignored — PASS")

    print(f"\n{'=' * 60}")
    print("Self-test complete!")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    self_test()
