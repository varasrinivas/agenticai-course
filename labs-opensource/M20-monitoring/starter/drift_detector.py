"""
M20 Lab - Step 1: Z-Score Drift Detector
=========================================
Pure algorithm — no LLM, no infrastructure. Run: python drift_detector.py
"""

import json
import math
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class DriftAlert:
    metric: str
    current_value: float
    baseline_mean: float
    baseline_std: float
    z_score: float
    direction: str    # "up" | "down"
    severity: str     # "warning" | "critical"


class RollingWindow:
    """(COMPLETE) Fixed-size FIFO of float samples."""

    def __init__(self, max_size: int):
        self.max_size = max_size
        self.data: list[float] = []

    def push(self, val: float) -> None:
        self.data.append(val)
        if len(self.data) > self.max_size:
            self.data.pop(0)

    @property
    def values(self) -> list[float]:
        return list(self.data)

    @property
    def size(self) -> int:
        return len(self.data)


def mean(arr: list[float]) -> float:
    return sum(arr) / len(arr)


def stddev(arr: list[float]) -> float:
    m = mean(arr)
    return math.sqrt(sum((v - m) ** 2 for v in arr) / len(arr))


class DriftDetector:
    """Tracks quality, tokens/query, and tool-call frequency for drift."""

    MIN_SAMPLES = 30  # small samples scream false alarms

    def __init__(self, window_size: int = 2016):  # 7 days at 5-min resolution
        self.quality_w = RollingWindow(window_size)
        self.tokens_w = RollingWindow(window_size)
        self.tool_freq_w = RollingWindow(window_size)

    def record(self, quality_score: float, tokens_used: float,
               tool_calls_made: int, max_tool_calls: int = 5) -> list[DriftAlert]:
        """(COMPLETE) Push samples, check all three metrics."""
        self.quality_w.push(quality_score)
        self.tokens_w.push(tokens_used)
        self.tool_freq_w.push(tool_calls_made / max(max_tool_calls, 1))

        alerts = [
            self.check_drift("quality_score", self.quality_w),
            self.check_drift("tokens_per_query", self.tokens_w),
            self.check_drift("tool_call_frequency", self.tool_freq_w),
        ]
        return [a for a in alerts if a is not None]

    def check_drift(self, metric: str, window: RollingWindow) -> Optional[DriftAlert]:
        """Z-score the LATEST sample against the rest of the window.

        TODO:
        1. If window.size < self.MIN_SAMPLES: return None
        2. current = window.values[-1]; history = window.values[:-1]
           ← compare against the window EXCLUDING the latest value
        3. m = mean(history); s = stddev(history)
        4. If s == 0: return None unless current != m — with constant history
           any difference is "infinite" drift; just return None for simplicity
        5. z = (current - m) / s
        6. If abs(z) < 2: return None
        7. Return DriftAlert(metric, current, m, s, z,
                             direction="up" if z > 0 else "down",
                             severity="critical" if abs(z) >= 3 else "warning")
        """
        pass  # Remove this line when you add your code


# ── Test harness (COMPLETE) ──
if __name__ == "__main__":
    import random

    random.seed(9)
    det = DriftDetector(window_size=200)

    print("Phase 1: 60 samples of STABLE behavior")
    stable_warnings = 0
    stable_criticals = 0
    for _ in range(60):
        alerts = det.record(
            quality_score=random.gauss(0.85, 0.03),
            tokens_used=random.gauss(900, 60),
            tool_calls_made=random.choice([1, 2, 2, 3]),
        )
        stable_warnings += sum(1 for a in alerts if a.severity == "warning")
        stable_criticals += sum(1 for a in alerts if a.severity == "critical")
    print(f"  Stable phase: {stable_warnings} warnings, {stable_criticals} criticals")
    print("  (A handful of 2-sigma warnings is EXPECTED — |z|>=2 fires ~5% of")
    print("   the time by pure chance. That's why only CRITICAL pages a human.)")

    print("\nPhase 2: DEGRADED behavior (quality tanks, tokens triple)")
    fired = []
    for i in range(5):
        alerts = det.record(
            quality_score=0.55,
            tokens_used=2800,
            tool_calls_made=5,
        )
        for a in alerts:
            fired.append(a)
            print(f"  [{a.severity.upper()}] {a.metric}: {a.current_value:.2f} "
                  f"vs baseline {a.baseline_mean:.2f} +/- {a.baseline_std:.2f} "
                  f"(z={a.z_score:+.1f}, {a.direction})")

    assert stable_criticals == 0, f"criticals during stable phase: {stable_criticals}"
    assert any(a.metric == "quality_score" and a.direction == "down"
               and a.severity == "critical" for a in fired), "quality drop not critical"
    assert any(a.metric == "tokens_per_query" and a.direction == "up"
               and a.severity == "critical" for a in fired), "token explosion not critical"
    print("\nAll drift checks passed.")
