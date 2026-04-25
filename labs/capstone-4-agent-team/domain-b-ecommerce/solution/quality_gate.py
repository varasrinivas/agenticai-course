"""
Circuit Breaker — B2B Ecommerce (Solution)
Tracks consecutive SLA violations. Trips after > 3 consecutive.
"""

import time
from typing import Optional


class CircuitBreaker:
    def __init__(self, name="sla_monitor", max_consecutive_failures=3, cooldown_seconds=60.0):
        self.name = name
        self.max_consecutive_failures = max_consecutive_failures
        self.cooldown_seconds = cooldown_seconds
        self._consecutive_failures = 0
        self._state = "closed"
        self._last_failure_time: Optional[float] = None
        self._total_successes = 0
        self._total_failures = 0

    @property
    def state(self):
        return self._state

    def record_success(self):
        self._consecutive_failures = 0
        self._total_successes += 1
        if self._state == "half_open":
            self._state = "closed"

    def record_failure(self):
        self._consecutive_failures += 1
        self._total_failures += 1
        self._last_failure_time = time.time()
        if self._consecutive_failures > self.max_consecutive_failures:
            if self._state != "open":
                self._state = "open"
                print(f"  [CIRCUIT BREAKER '{self.name}'] TRIPPED after {self._consecutive_failures} consecutive failures!")

    def is_tripped(self):
        if self._state == "closed":
            return False
        if self._state == "open":
            if self._last_failure_time and (time.time() - self._last_failure_time >= self.cooldown_seconds):
                self._state = "half_open"
                return False
            return True
        return False  # half_open

    def reset(self):
        self._consecutive_failures = 0
        self._state = "closed"
        self._last_failure_time = None

    def get_status(self):
        return {"name": self.name, "state": self._state, "consecutive_failures": self._consecutive_failures, "max": self.max_consecutive_failures, "total_successes": self._total_successes, "total_failures": self._total_failures}
