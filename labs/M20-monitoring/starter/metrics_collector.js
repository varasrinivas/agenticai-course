/**
 * M20 Lab — Monitoring: Metrics Collector (Starter)
 * ==================================================
 * Build a metrics collector that tracks request count, latency
 * percentiles, token costs, error rates, and per-tool statistics
 * for a UCC filing agent.
 *
 * KEY CONCEPT: Raw logs are noise. Metrics are signal. A good
 * collector turns thousands of individual requests into a handful
 * of numbers (p95 latency, error rate, cost/hour) that tell you
 * whether your agent is healthy or sick.
 *
 * Usage:
 *     node metrics_collector.js
 */

// =============================================================================
// CLAUDE SONNET PRICING (as of 2025)
// =============================================================================

const SONNET_INPUT_COST_PER_MILLION = 3.0;   // $3.00 per 1M input tokens
const SONNET_OUTPUT_COST_PER_MILLION = 15.0;  // $15.00 per 1M output tokens

// =============================================================================
// METRICS COLLECTOR
// =============================================================================

class MetricsCollector {
  /**
   * Collects and aggregates metrics from agent requests.
   *
   * Tracks:
   * - Request count and error rate
   * - Latency percentiles (p50, p75, p90, p95, p99)
   * - Token usage and cost estimates
   * - Per-tool call counts, failure rates, and durations
   * - Throughput (requests per minute)
   */

  constructor() {
    this.requests = [];
    this.startTime = Date.now();
  }

  /**
   * Record a single request's metrics.
   *
   * @param {number} durationMs - How long the request took in milliseconds
   * @param {number} inputTokens - Number of input tokens consumed
   * @param {number} outputTokens - Number of output tokens generated
   * @param {boolean} success - Whether the request completed successfully
   * @param {Array} toolsUsed - List of tool calls [{name, duration_ms, success}]
   */
  recordRequest(durationMs, inputTokens, outputTokens, success, toolsUsed = []) {
    // TODO: Create a request record object and push to this.requests
    // HINT: Include timestamp: Date.now()
  }

  /** Return total number of recorded requests. */
  getRequestCount() {
    // TODO: Return the length of this.requests
  }

  /**
   * Calculate latency percentiles from recorded durations.
   *
   * @returns {Object} {p50, p75, p90, p95, p99} in milliseconds
   */
  getLatencyPercentiles() {
    // TODO: Implement percentile calculation
    // HINT: Extract all durationMs values, sort numerically
    // HINT: For percentile P: index = Math.ceil(P / 100 * N) - 1
    // HINT: Clamp index to [0, N-1]
    // HINT: Return {p50: ..., p75: ..., p90: ..., p95: ..., p99: ...}
    // HINT: If no requests, return all zeros
  }

  /**
   * Calculate error rate as a percentage.
   * @returns {number} Between 0.0 and 100.0
   */
  getErrorRate() {
    // TODO: Count failed requests / total requests * 100
    // HINT: Return 0.0 if no requests
  }

  /**
   * Calculate token usage statistics and cost estimates.
   *
   * @returns {Object} {totalInput, totalOutput, avgInputPerRequest,
   *                     avgOutputPerRequest, costEstimate, costPerHour}
   */
  getTokenStats() {
    // TODO: Sum up all input/output tokens, compute cost
    // HINT: cost = (totalInput / 1e6 * SONNET_INPUT_COST_PER_MILLION)
    //            + (totalOutput / 1e6 * SONNET_OUTPUT_COST_PER_MILLION)
    // HINT: elapsedHours = (Date.now() - this.startTime) / 3600000
    // HINT: Return all zeros if no requests
  }

  /**
   * Calculate per-tool statistics.
   *
   * @returns {Object} {toolName: {calls, failures, failureRate, avgDurationMs}}
   */
  getToolStats() {
    // TODO: Iterate through all requests and their toolsUsed
    // HINT: Build an object keyed by tool name
    // HINT: Track calls, failures, totalDuration per tool
    // HINT: failureRate = failures / calls * 100
  }

  /**
   * Calculate requests per minute over the last N minutes.
   *
   * @param {number} windowMinutes - How far back to look (default 5)
   * @returns {number} Requests per minute
   */
  getThroughput(windowMinutes = 5) {
    // TODO: Count requests in the last windowMinutes
    // HINT: cutoff = Date.now() - (windowMinutes * 60 * 1000)
  }

  /** Clear all recorded metrics and reset start time. */
  reset() {
    // TODO: Clear this.requests, reset this.startTime
  }

  /** Export all metrics as a single object. */
  toDict() {
    // TODO: Return combined metrics object
    // {
    //   requestCount, errorRate, latency: this.getLatencyPercentiles(),
    //   tokens: this.getTokenStats(), tools: this.getToolStats(),
    //   throughputRpm: this.getThroughput(),
    //   uptimeSeconds: (Date.now() - this.startTime) / 1000,
    // }
  }
}

// =============================================================================
// SELF-TEST
// =============================================================================

function selfTest() {
  console.log("=".repeat(60));
  console.log("M20 Metrics Collector — Self-Test");
  console.log("=".repeat(60));

  const collector = new MetricsCollector();
  const toolNames = ["search_filings", "get_details", "calc_risk"];

  // Simulate 100 requests
  for (let i = 0; i < 100; i++) {
    let duration;
    if (Math.random() < 0.05) {
      duration = 3000 + Math.random() * 5000;
    } else if (Math.random() < 0.15) {
      duration = 1000 + Math.random() * 2000;
    } else {
      duration = 100 + Math.random() * 400;
    }

    const success = Math.random() > 0.08;
    const inputTokens = Math.floor(500 + Math.random() * 1500);
    const outputTokens = Math.floor(200 + Math.random() * 1300);

    const numTools = 1 + Math.floor(Math.random() * 3);
    const tools = [];
    for (let j = 0; j < numTools; j++) {
      tools.push({
        name: toolNames[Math.floor(Math.random() * toolNames.length)],
        duration_ms: 5 + Math.random() * 95,
        success: Math.random() > 0.05,
      });
    }

    collector.recordRequest(duration, inputTokens, outputTokens, success, tools);
  }

  console.log(`\nRequests recorded: ${collector.getRequestCount()}`);
  console.log(`Error rate: ${collector.getErrorRate().toFixed(1)}%`);

  const latency = collector.getLatencyPercentiles();
  console.log("\nLatency percentiles (ms):");
  for (const key of ["p50", "p75", "p90", "p95", "p99"]) {
    console.log(`  ${key}: ${Math.round(latency[key])}`);
  }

  const tokens = collector.getTokenStats();
  console.log("\nToken stats:");
  console.log(`  Total input:  ${tokens.totalInput.toLocaleString()}`);
  console.log(`  Total output: ${tokens.totalOutput.toLocaleString()}`);
  console.log(`  Cost estimate: $${tokens.costEstimate.toFixed(4)}`);

  const tools = collector.getToolStats();
  console.log("\nTool stats:");
  for (const [name, stats] of Object.entries(tools)) {
    console.log(
      `  ${name}: ${stats.calls} calls, ` +
      `${stats.failureRate.toFixed(1)}% fail, ` +
      `avg ${Math.round(stats.avgDurationMs)}ms`
    );
  }

  console.log(`\nThroughput: ${collector.getThroughput().toFixed(1)} req/min`);

  // Verify monotonic percentiles
  const ok =
    latency.p50 <= latency.p75 &&
    latency.p75 <= latency.p90 &&
    latency.p90 <= latency.p95 &&
    latency.p95 <= latency.p99;
  if (!ok) throw new Error("Percentiles should be monotonically increasing!");
  console.log("\n✅ Percentiles are monotonically increasing — PASS");

  console.log(`\n${"=".repeat(60)}`);
  console.log("Self-test complete!");
  console.log("=".repeat(60));
}

// Export for use by other modules
export { MetricsCollector, SONNET_INPUT_COST_PER_MILLION, SONNET_OUTPUT_COST_PER_MILLION };

// Run self-test if executed directly
const isMain = process.argv[1] && (
  process.argv[1].endsWith("metrics_collector.js")
);
if (isMain) {
  selfTest();
}
