/**
 * M17: Circuit Breaker — Solution
 * Implements the circuit breaker pattern to halt agents after consecutive failures.
 * States: CLOSED (normal) -> OPEN (tripped) -> HALF_OPEN (testing recovery).
 */

export const CircuitState = Object.freeze({
  CLOSED: "closed",
  OPEN: "open",
  HALF_OPEN: "half_open",
});

export class CircuitBreaker {
  constructor(failureThreshold = 3, resetTimeout = 60.0) {
    this.failureThreshold = failureThreshold;
    this.resetTimeout = resetTimeout;
    this.state = CircuitState.CLOSED;
    this.failureCount = 0;
    this.successCount = 0;
    this.lastFailureTime = null;
    this.lastStateChange = Date.now();
  }

  recordSuccess() {
    this.successCount += 1;

    if (this.state === CircuitState.CLOSED) {
      this.failureCount = 0;
    } else if (this.state === CircuitState.HALF_OPEN) {
      this.failureCount = 0;
      this._transition(CircuitState.CLOSED);
    }
  }

  recordFailure() {
    this.failureCount += 1;
    this.lastFailureTime = Date.now();

    if (this.state === CircuitState.CLOSED) {
      if (this.failureCount >= this.failureThreshold) {
        this._transition(CircuitState.OPEN);
      }
    } else if (this.state === CircuitState.HALF_OPEN) {
      this._transition(CircuitState.OPEN);
    }
  }

  canExecute() {
    if (this.state === CircuitState.CLOSED) {
      return true;
    }

    if (this.state === CircuitState.OPEN) {
      if (this.lastFailureTime === null) return true;
      const elapsed = (Date.now() - this.lastFailureTime) / 1000;
      if (elapsed >= this.resetTimeout) {
        this._transition(CircuitState.HALF_OPEN);
        return true;
      }
      return false;
    }

    // HALF_OPEN
    return true;
  }

  getState() {
    let timeSinceLastFailure = null;
    let timeUntilRetry = null;

    if (this.lastFailureTime !== null) {
      timeSinceLastFailure = parseFloat(((Date.now() - this.lastFailureTime) / 1000).toFixed(2));
    }

    if (this.state === CircuitState.OPEN && this.lastFailureTime !== null) {
      const remaining = this.resetTimeout - (Date.now() - this.lastFailureTime) / 1000;
      timeUntilRetry = parseFloat(Math.max(0, remaining).toFixed(2));
    }

    return {
      state: this.state,
      failureCount: this.failureCount,
      successCount: this.successCount,
      failureThreshold: this.failureThreshold,
      timeSinceLastFailure,
      timeUntilRetry,
    };
  }

  _transition(newState) {
    this.state = newState;
    this.lastStateChange = Date.now();
  }

  forceOpen() {
    this.lastFailureTime = Date.now();
    this._transition(CircuitState.OPEN);
  }
}

// ── Self-Test ───────────────────────────────────────────────
const isMain = process.argv[1] && (
  process.argv[1].endsWith("circuit_breaker.js") ||
  process.argv[1].endsWith("circuit_breaker.mjs")
);

if (isMain) {
  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

  console.log("=".repeat(60));
  console.log("M17 Circuit Breaker — Self-Test");
  console.log("=".repeat(60));

  const cb = new CircuitBreaker(3, 2.0);

  let state = cb.getState();
  console.log(`\nTest 1 — Initial state: ${state.state}`);
  console.log(`  Can execute: ${cb.canExecute()}`);

  cb.recordSuccess();
  cb.recordSuccess();
  state = cb.getState();
  console.log(`\nTest 2 — After 2 successes: ${state.state}`);
  console.log(`  Success count: ${state.successCount}`);

  console.log(`\nTest 3 — Recording failures:`);
  for (let i = 0; i < 3; i++) {
    cb.recordFailure();
    state = cb.getState();
    console.log(`  Failure ${i + 1}: state=${state.state}, failures=${state.failureCount}`);
  }

  state = cb.getState();
  console.log(`\nTest 4 — After 3 failures:`);
  console.log(`  State: ${state.state}`);
  console.log(`  Can execute: ${cb.canExecute()}`);
  console.log(`  Time until retry: ${state.timeUntilRetry ?? "N/A"}`);

  console.log(`\nTest 5 — Waiting for reset timeout (2 seconds)...`);
  await sleep(2100);
  console.log(`  Can execute: ${cb.canExecute()}`);
  state = cb.getState();
  console.log(`  State after timeout: ${state.state}`);

  cb.recordSuccess();
  state = cb.getState();
  console.log(`\nTest 6 — After recovery success:`);
  console.log(`  State: ${state.state}`);
  console.log(`  Failure count: ${state.failureCount}`);

  console.log("\n" + "=".repeat(60));
  console.log("All tests complete.");
  console.log("=".repeat(60));
}
