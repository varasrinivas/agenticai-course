"""
M17: Circuit Breaker — Starter
Implements the circuit breaker pattern to halt agents after consecutive failures.
States: CLOSED (normal) → OPEN (tripped) → HALF_OPEN (testing recovery).
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
    - HALF_OPEN: One call allowed. Success → CLOSED, Failure → OPEN.
    """

    def __init__(self, failure_threshold: int = 3, reset_timeout: float = 60.0):
        """
        Args:
            failure_threshold: Number of consecutive failures before tripping (default 3).
            reset_timeout: Seconds to wait before allowing a test call (default 60).
        """
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout

        # TODO 1: Initialize state tracking:
        #   self.state = CircuitState.CLOSED
        #   self.failure_count = 0
        #   self.success_count = 0
        #   self.last_failure_time = None
        #   self.last_state_change = time.time()

    def record_success(self):
        """
        Record a successful operation.

        - In CLOSED state: reset failure counter.
        - In HALF_OPEN state: circuit recovered — move to CLOSED.
        """
        # TODO 2: Handle success in CLOSED state (reset failure_count, increment success_count).
        # Handle success in HALF_OPEN state (transition to CLOSED, reset counters).
        pass

    def record_failure(self):
        """
        Record a failed operation.

        - In CLOSED state: increment failure count. If threshold hit, trip to OPEN.
        - In HALF_OPEN state: test call failed — go back to OPEN.
        """
        # TODO 3: Handle failure in CLOSED state: increment failure_count,
        # set last_failure_time. If failure_count >= threshold, transition to OPEN.
        # Handle failure in HALF_OPEN state: transition back to OPEN.
        pass

    def can_execute(self) -> bool:
        """
        Check if an operation is allowed under the current circuit state.

        Returns True if:
        - State is CLOSED (always allowed)
        - State is OPEN but reset_timeout has elapsed (transitions to HALF_OPEN, allows one call)
        - State is HALF_OPEN (one test call allowed)

        Returns False if:
        - State is OPEN and timeout hasn't elapsed
        """
        # TODO 4: Implement the state machine logic.
        # If CLOSED: return True.
        # If OPEN: check if (current_time - last_failure_time) >= reset_timeout.
        #          If yes, transition to HALF_OPEN and return True.
        #          If no, return False.
        # If HALF_OPEN: return True.
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
                "time_until_retry": float or None  # seconds until HALF_OPEN (if OPEN)
            }
        """
        # TODO 5: Build and return the state dict.
        # time_since_last_failure: seconds since last_failure_time (None if no failures).
        # time_until_retry: if OPEN, seconds remaining before reset_timeout expires (None otherwise).
        return {
            "state": "closed",
            "failure_count": 0,
            "success_count": 0,
            "failure_threshold": self.failure_threshold,
            "time_since_last_failure": None,
            "time_until_retry": None,
        }

    def _transition(self, new_state: CircuitState):
        """Internal: transition to a new state and record the time."""
        # TODO 6: Set self.state = new_state and self.last_state_change = time.time()
        pass

    def force_open(self):
        """Manually trip the circuit breaker (for testing or emergency shutdown)."""
        # TODO 7: Transition to OPEN and set last_failure_time to now.
        pass


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
    print("Self-test complete. Fill in TODOs to see correct state transitions.")
    print("=" * 60)
