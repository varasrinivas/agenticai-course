"""
Circuit Breaker — Quality Gate for the Healthcare Pre-Auth Pipeline (Solution)

Fully implemented circuit breaker with CLOSED, OPEN, and HALF_OPEN states.
"""

import time
from collections import deque
from typing import Optional


class CircuitBreaker:
    """
    Circuit breaker that monitors error rates and halts processing
    when the threshold is exceeded.
    """

    def __init__(
        self,
        name: str = "default",
        failure_threshold: float = 0.10,
        window_size: int = 20,
        cooldown_seconds: float = 60.0,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.window_size = window_size
        self.cooldown_seconds = cooldown_seconds

        self._results: deque[bool] = deque(maxlen=window_size)
        self._state = "closed"
        self._last_failure_time: Optional[float] = None
        self._total_successes = 0
        self._total_failures = 0

    @property
    def state(self) -> str:
        return self._state

    @property
    def failure_rate(self) -> float:
        if len(self._results) == 0:
            return 0.0
        failures = sum(1 for r in self._results if not r)
        return failures / len(self._results)

    def record_success(self) -> None:
        self._results.append(True)
        self._total_successes += 1
        if self._state == "half_open":
            self._state = "closed"
            print(f"  [CIRCUIT BREAKER '{self.name}'] Half-open -> Closed (recovery confirmed)")

    def record_failure(self) -> None:
        self._results.append(False)
        self._total_failures += 1
        self._last_failure_time = time.time()

        if self.failure_rate > self.failure_threshold and len(self._results) >= 3:
            if self._state != "open":
                self._state = "open"
                print(
                    f"  [CIRCUIT BREAKER '{self.name}'] TRIPPED! "
                    f"Failure rate {self.failure_rate:.1%} > threshold {self.failure_threshold:.1%}"
                )

    def is_tripped(self) -> bool:
        if self._state == "closed":
            return False

        if self._state == "open":
            if self._last_failure_time is not None:
                elapsed = time.time() - self._last_failure_time
                if elapsed >= self.cooldown_seconds:
                    self._state = "half_open"
                    print(f"  [CIRCUIT BREAKER '{self.name}'] Open -> Half-open (cooldown elapsed)")
                    return False
            return True

        # half_open — allow test request
        return False

    def reset(self) -> None:
        self._results.clear()
        self._state = "closed"
        self._last_failure_time = None

    def get_status(self) -> dict:
        return {
            "name": self.name,
            "state": self._state,
            "failure_rate": round(self.failure_rate, 4),
            "failure_threshold": self.failure_threshold,
            "window_size": self.window_size,
            "results_in_window": len(self._results),
            "total_successes": self._total_successes,
            "total_failures": self._total_failures,
        }
