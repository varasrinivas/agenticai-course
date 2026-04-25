"""
Tests for the CircuitBreaker (quality_gate.py) — Ecommerce Domain B.

The ecommerce circuit breaker tracks consecutive failures (not a sliding
window rate). It trips when consecutive failures exceed max_consecutive_failures.
"""

import os
import sys
import time

import pytest

SOLUTION_DIR = os.path.join(os.path.dirname(__file__), "..", "solution")
sys.path.insert(0, SOLUTION_DIR)

from quality_gate import CircuitBreaker


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------
@pytest.fixture
def breaker():
    """Return a fresh CircuitBreaker with a small threshold for fast testing."""
    return CircuitBreaker(
        name="test_sla",
        max_consecutive_failures=3,
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


# ---------------------------------------------------------------------------
# Test: recording successes never trips
# ---------------------------------------------------------------------------
class TestRecordSuccess:
    def test_successes_do_not_trip(self, breaker):
        for _ in range(20):
            breaker.record_success()
        assert breaker.is_tripped() is False
        assert breaker.state == "closed"

    def test_success_resets_consecutive_failures(self, breaker):
        breaker.record_failure()
        breaker.record_failure()
        breaker.record_success()
        # consecutive count should be reset, so 1 more failure should NOT trip
        breaker.record_failure()
        assert breaker.state == "closed"


# ---------------------------------------------------------------------------
# Test: enough consecutive failures trip the breaker
# ---------------------------------------------------------------------------
class TestRecordFailure:
    def test_consecutive_failures_trip(self, breaker):
        """max_consecutive_failures=3, trips after > 3 consecutive = 4 failures."""
        breaker.record_failure()
        breaker.record_failure()
        breaker.record_failure()
        assert breaker.state == "closed"  # exactly 3, not > 3 yet

        breaker.record_failure()  # 4th consecutive -> trips
        assert breaker.state == "open"
        assert breaker.is_tripped() is True

    def test_interleaved_success_prevents_trip(self, breaker):
        """A success in between resets the consecutive counter."""
        breaker.record_failure()
        breaker.record_failure()
        breaker.record_success()  # reset
        breaker.record_failure()
        breaker.record_failure()
        breaker.record_failure()
        assert breaker.state == "closed"  # only 3 consecutive, not > 3


# ---------------------------------------------------------------------------
# Test: reset clears the breaker
# ---------------------------------------------------------------------------
class TestReset:
    def test_reset_clears_open_state(self, breaker):
        for _ in range(5):
            breaker.record_failure()
        assert breaker.state == "open"

        breaker.reset()
        assert breaker.state == "closed"
        assert breaker.is_tripped() is False

    def test_reset_clears_consecutive_count(self, breaker):
        breaker.record_failure()
        breaker.record_failure()
        breaker.reset()
        status = breaker.get_status()
        assert status["consecutive_failures"] == 0


# ---------------------------------------------------------------------------
# Test: cooldown transitions open -> half_open -> closed
# ---------------------------------------------------------------------------
class TestCooldown:
    def test_half_open_after_cooldown(self, breaker):
        for _ in range(5):
            breaker.record_failure()
        assert breaker.state == "open"

        time.sleep(0.15)
        assert breaker.is_tripped() is False
        assert breaker.state == "half_open"

    def test_half_open_to_closed_on_success(self, breaker):
        for _ in range(5):
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
            "name", "state", "consecutive_failures", "max",
            "total_successes", "total_failures",
        }
        assert expected_keys == set(status.keys())

    def test_status_name(self, breaker):
        assert breaker.get_status()["name"] == "test_sla"
