/**
 * M17: Circuit Breaker — Starter
 * Implements the circuit breaker pattern to halt agents after consecutive failures.
 * States: CLOSED (normal) -> OPEN (tripped) -> HALF_OPEN (testing recovery).
 */

export const CircuitState = Object.freeze({
  CLOSED: "closed",
  OPEN: "open",
  HALF_OPEN: "half_open",
});

export class CircuitBreaker {
  /**
   * @param {number} failureThreshold - Consecutive failures before tripping (default 3).
   * @param {number} resetTimeout - Seconds to wait before allowing a test call (default 60).
   */
  constructor(failureThreshold = 3, resetTimeout = 60.0) {
    this.failureThreshold = failureThreshold;
    this.resetTimeout = resetTimeout;

    // TODO 1: Initialize state tracking:
    //   this.state = CircuitState.CLOSED;
    //   this.failureCount = 0;
    //   this.successCount = 0;
    //   this.lastFailureTime = null;
    //   this.lastStateChange = Date.now();
  }

  /** Record a successful operation. */
  recordSuccess() {
    // TODO 2: Handle success in CLOSED state (reset failureCount, increment successCount).
    // Handle success in HALF_OPEN state (transition to CLOSED, reset counters).
  }

  /** Record a failed operation. */
  recordFailure() {
    // TODO 3: Handle failure in CLOSED state: increment failureCount,
    // set lastFailureTime. If failureCount >= threshold, transition to OPEN.
    // Handle failure in HALF_OPEN state: transition back to OPEN.
  }

  /**
   * Check if an operation is allowed under the current circuit state.
   * @returns {boolean}
   */
  canExecute() {
    // TODO 4: Implement the state machine logic.
    // If CLOSED: return true.
    // If OPEN: check if (Date.now() - lastFailureTime) / 1000 >= resetTimeout.
    //          If yes, transition to HALF_OPEN and return true.
    //          If no, return false.
    // If HALF_OPEN: return true.
    return true;
  }

  /**
   * Return current circuit breaker state with details.
   * @returns {Object}
   */
  getState() {
    // TODO 5: Build and return the state object.
    return {
      state: "closed",
      failureCount: 0,
      successCount: 0,
      failureThreshold: this.failureThreshold,
      timeSinceLastFailure: null,
      timeUntilRetry: null,
    };
  }

  /** Internal: transition to a new state. */
  _transition(newState) {
    // TODO 6: Set this.state = newState and this.lastStateChange = Date.now()
  }

  /** Manually trip the circuit breaker. */
  forceOpen() {
    // TODO 7: Transition to OPEN and set lastFailureTime to Date.now().
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
  console.log(`  State after timeout: ${cb.getState().state}`);
  console.log(`  Can execute: ${cb.canExecute()}`);
  state = cb.getState();
  console.log(`  State: ${state.state}`);

  cb.recordSuccess();
  state = cb.getState();
  console.log(`\nTest 6 — After recovery success:`);
  console.log(`  State: ${state.state}`);
  console.log(`  Failure count: ${state.failureCount}`);

  console.log("\n" + "=".repeat(60));
  console.log("Self-test complete. Fill in TODOs to see correct state transitions.");
  console.log("=".repeat(60));
}
