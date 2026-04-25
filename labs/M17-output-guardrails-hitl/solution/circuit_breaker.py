"""
M17: Circuit Breaker — Solution
Implements the circuit breaker pattern to halt agents after consecutive failures.
States: CLOSED (normal) -> OPEN (tripped) -> HALF_OPEN (testing recovery).
"""
import time
from enum import Enum


class CircuitState(Enum):
    CLOSED = "closed"       # Normal operation — requests pass through
    OPEN = "open"           # Tripped — all requests rejected
    HALF_OPEN = "half_open" # Testing — one request allowed to test recovery


class CircuitBreaker:
    """
    Circuit breaker that trips after consecutive failures and resets after a timeout.

    - CLOSED: All calls proceed. Failures are counted.
    - OPEN: All calls rejected immediately. After reset_timeout seconds, moves to HALF_OPEN.
    - HALF_OPEN: One call allowed. Success -> CLOSED, Failure -> OPEN.
    """

    def __init__(self, failure_threshold: int = 3, reset_timeout: float = 60.0):
        """
        Args:
            failure_threshold: Number of consecutive failures before tripping (default 3).
            reset_timeout: Seconds to wait before allowing a test call (default 60).
        """
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.last_state_change = time.time()

    def record_success(self):
        """
        Record a successful operation.

        - In CLOSED state: reset failure counter.
        - In HALF_OPEN state: circuit recovered — move to CLOSED.
        """
        self.success_count += 1

        if self.state == CircuitState.CLOSED:
            self.failure_count = 0
        elif self.state == CircuitState.HALF_OPEN:
            self.failure_count = 0
            self._transition(CircuitState.CLOSED)

    def record_failure(self):
        """
        Record a failed operation.

        - In CLOSED state: increment failure count. If threshold hit, trip to OPEN.
        - In HALF_OPEN state: test call failed — go back to OPEN.
        """
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.state == CircuitState.CLOSED:
            if self.failure_count >= self.failure_threshold:
                self._transition(CircuitState.OPEN)
        elif self.state == CircuitState.HALF_OPEN:
            self._transition(CircuitState.OPEN)

    def can_execute(self) -> bool:
        """
        Check if an operation is allowed under the current circuit state.

        Returns True if:
        - State is CLOSED (always allowed)
        - State is OPEN but reset_timeout has elapsed (transitions to HALF_OPEN)
        - State is HALF_OPEN (one test call allowed)

        Returns False if:
        - State is OPEN and timeout hasn't elapsed
        """
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            if self.last_failure_time is None:
                return True
            elapsed = time.time() - self.last_failure_time
            if elapsed >= self.reset_timeout:
                self._transition(CircuitState.HALF_OPEN)
                return True
            return False

        # HALF_OPEN — allow one test call
        return True

    def get_state(self) -> dict:
        """
        Return current circuit breaker state with details.

        Returns:
            {
                "state": str,
                "failure_count": int,
                "success_count": int,
                "failure_threshold": int,
                "time_since_last_failure": float or None,
                "time_until_retry": float or None
            }
        """
        time_since = None
        time_until = None

        if self.last_failure_time is not None:
            time_since = round(time.time() - self.last_failure_time, 2)

        if self.state == CircuitState.OPEN and self.last_failure_time is not None:
            remaining = self.reset_timeout - (time.time() - self.last_failure_time)
            time_until = round(max(0, remaining), 2)

        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "failure_threshold": self.failure_threshold,
            "time_since_last_failure": time_since,
            "time_until_retry": time_until,
        }

    def _transition(self, new_state: CircuitState):
        """Internal: transition to a new state and record the time."""
        self.state = new_state
        self.last_state_change = time.time()

    def force_open(self):
        """Manually trip the circuit breaker (for testing or emergency shutdown)."""
        self.last_failure_time = time.time()
        self._transition(CircuitState.OPEN)


# ── Self-Test ───────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("M17 Circuit Breaker — Self-Test")
    print("=" * 60)

    # Use a short timeout for testing
    cb = CircuitBreaker(failure_threshold=3, reset_timeout=2.0)

    # Test 1: Normal operation (CLOSED)
    state = cb.get_state()
    print(f"\nTest 1 — Initial state: {state['state']}")
    print(f"  Can execute: {cb.can_execute()}")

    # Test 2: Record some successes
    cb.record_success()
    cb.record_success()
    state = cb.get_state()
    print(f"\nTest 2 — After 2 successes: {state['state']}")
    print(f"  Success count: {state['success_count']}")

    # Test 3: Record failures up to threshold
    print(f"\nTest 3 — Recording failures:")
    for i in range(3):
        cb.record_failure()
        state = cb.get_state()
        print(f"  Failure {i+1}: state={state['state']}, failures={state['failure_count']}")

    # Test 4: Circuit should be OPEN now
    can_exec = cb.can_execute()
    state = cb.get_state()
    print(f"\nTest 4 — After 3 failures:")
    print(f"  State: {state['state']}")
    print(f"  Can execute: {can_exec}")
    print(f"  Time until retry: {state.get('time_until_retry', 'N/A')}")

    # Test 5: Wait for timeout, then test recovery
    print(f"\nTest 5 — Waiting for reset timeout (2 seconds)...")
    time.sleep(2.1)
    can_exec = cb.can_execute()
    state = cb.get_state()
    print(f"  State after timeout: {state['state']}")
    print(f"  Can execute: {can_exec}")

    # Test 6: Successful recovery
    cb.record_success()
    state = cb.get_state()
    print(f"\nTest 6 — After recovery success:")
    print(f"  State: {state['state']}")
    print(f"  Failure count: {state['failure_count']}")

    print("\n" + "=" * 60)
    print("All tests complete.")
    print("=" * 60)
