"""
Tests for the CircuitBreaker (quality_gate.py) — Healthcare Domain A.

Validates circuit breaker state transitions: closed -> open -> half_open -> closed,
recording successes/failures, tripping at threshold, and reset behaviour.
"""

import os
import sys
import time

import pytest

SOLUTION_DIR = os.path.join(os.path.dirname(__file__), "..", "solution")
sys.path.insert(0, SOLUTION_DIR)

from quality_gate import CircuitBreaker


# ---------------------------------------------------------------------------
# Fixture: fresh breaker with tight settings for fast testing
# ---------------------------------------------------------------------------
@pytest.fixture
def breaker():
    """Return a fresh CircuitBreaker with a small window for easy testing."""
    return CircuitBreaker(
        name="test_breaker",
        failure_threshold=0.50,
        window_size=4,
        cooldown_seconds=0.1,
    )


# ---------------------------------------------------------------------------
# Test: fresh breaker starts closed and is NOT tripped
# ---------------------------------------------------------------------------
class TestFreshBreaker:
    def test_initial_state_is_closed(self, breaker):
        assert breaker.state == "closed"

    def test_initial_not_tripped(self, breaker):
        assert breaker.is_tripped() is False

    def test_initial_failure_rate_is_zero(self, breaker):
        assert breaker.failure_rate == 0.0


# ---------------------------------------------------------------------------
# Test: recording successes never trips
# ---------------------------------------------------------------------------
class TestRecordSuccess:
    def test_successes_do_not_trip(self, breaker):
        for _ in range(20):
            breaker.record_success()
        assert breaker.is_tripped() is False
        assert breaker.state == "closed"

    def test_success_count_tracked(self, breaker):
        breaker.record_success()
        breaker.record_success()
        status = breaker.get_status()
        assert status["total_successes"] == 2
        assert status["total_failures"] == 0


# ---------------------------------------------------------------------------
# Test: enough failures trip the breaker
# ---------------------------------------------------------------------------
class TestRecordFailure:
    def test_failures_trip_breaker(self, breaker):
        """With threshold 0.50 and window 4, 3 failures out of 3 (100%) should trip."""
        breaker.record_failure()
        breaker.record_failure()
        breaker.record_failure()
        assert breaker.state == "open"
        assert breaker.is_tripped() is True

    def test_mixed_below_threshold_does_not_trip(self, breaker):
        """2 successes + 1 failure = 33% < 50% threshold, should NOT trip."""
        breaker.record_success()
        breaker.record_success()
        breaker.record_failure()
        assert breaker.state == "closed"
        assert breaker.is_tripped() is False

    def test_failure_rate_calculated(self, breaker):
        breaker.record_success()
        breaker.record_failure()
        assert breaker.failure_rate == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# Test: reset clears the breaker
# ---------------------------------------------------------------------------
class TestReset:
    def test_reset_clears_open_state(self, breaker):
        # Trip the breaker first
        breaker.record_failure()
        breaker.record_failure()
        breaker.record_failure()
        assert breaker.state == "open"

        breaker.reset()
        assert breaker.state == "closed"
        assert breaker.is_tripped() is False
        assert breaker.failure_rate == 0.0

    def test_reset_clears_window(self, breaker):
        breaker.record_failure()
        breaker.record_failure()
        breaker.reset()
        status = breaker.get_status()
        assert status["results_in_window"] == 0


# ---------------------------------------------------------------------------
# Test: cooldown transitions open -> half_open -> closed
# ---------------------------------------------------------------------------
class TestCooldown:
    def test_half_open_after_cooldown(self, breaker):
        """After cooldown elapsed, is_tripped() should return False and state = half_open."""
        breaker.record_failure()
        breaker.record_failure()
        breaker.record_failure()
        assert breaker.state == "open"

        # Wait for cooldown (0.1s)
        time.sleep(0.15)
        assert breaker.is_tripped() is False
        assert breaker.state == "half_open"

    def test_half_open_to_closed_on_success(self, breaker):
        """A success in half_open state should transition to closed."""
        breaker.record_failure()
        breaker.record_failure()
        breaker.record_failure()
        time.sleep(0.15)
        breaker.is_tripped()  # triggers half_open
        assert breaker.state == "half_open"

        breaker.record_success()
        assert breaker.state == "closed"


# ---------------------------------------------------------------------------
# Test: get_status returns expected keys
# ---------------------------------------------------------------------------
class TestGetStatus:
    def test_status_keys(self, breaker):
        status = breaker.get_status()
        expected_keys = {
            "name", "state", "failure_rate", "failure_threshold",
            "window_size", "results_in_window", "total_successes", "total_failures",
        }
        assert expected_keys == set(status.keys())

    def test_status_name(self, breaker):
        assert breaker.get_status()["name"] == "test_breaker"
