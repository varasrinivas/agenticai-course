/**
 * M20 Lab — Monitoring: Metrics Collector (Solution)
 * ===================================================
 * Complete implementation of the metrics collector.
 *
 * Usage:
 *     node metrics_collector.js
 */

const SONNET_INPUT_COST_PER_MILLION = 3.0;
const SONNET_OUTPUT_COST_PER_MILLION = 15.0;

class MetricsCollector {
  constructor() {
    this.requests = [];
    this.startTime = Date.now();
  }

  recordRequest(durationMs, inputTokens, outputTokens, success, toolsUsed = []) {
    this.requests.push({
      timestamp: Date.now(),
      durationMs,
      inputTokens,
      outputTokens,
      success,
      toolsUsed: toolsUsed || [],
    });
  }

  getRequestCount() {
    return this.requests.length;
  }

  getLatencyPercentiles() {
    if (this.requests.length === 0) {
      return { p50: 0, p75: 0, p90: 0, p95: 0, p99: 0 };
    }

    const durations = this.requests.map((r) => r.durationMs).sort((a, b) => a - b);
    const n = durations.length;

    function percentile(p) {
      const index = Math.max(0, Math.min(Math.ceil((p / 100) * n) - 1, n - 1));
      return durations[index];
    }

    return {
      p50: percentile(50),
      p75: percentile(75),
      p90: percentile(90),
      p95: percentile(95),
      p99: percentile(99),
    };
  }

  getErrorRate() {
    if (this.requests.length === 0) return 0.0;
    const failed = this.requests.filter((r) => !r.success).length;
    return (failed / this.requests.length) * 100.0;
  }

  getTokenStats() {
    if (this.requests.length === 0) {
      return {
        totalInput: 0, totalOutput: 0,
        avgInputPerRequest: 0, avgOutputPerRequest: 0,
        costEstimate: 0, costPerHour: 0,
      };
    }

    const totalInput = this.requests.reduce((s, r) => s + r.inputTokens, 0);
    const totalOutput = this.requests.reduce((s, r) => s + r.outputTokens, 0);
    const n = this.requests.length;

    const cost =
      (totalInput / 1e6) * SONNET_INPUT_COST_PER_MILLION +
      (totalOutput / 1e6) * SONNET_OUTPUT_COST_PER_MILLION;

    const elapsedHours = (Date.now() - this.startTime) / 3600000;
    const costPerHour = elapsedHours > 0 ? cost / elapsedHours : 0;

    return {
      totalInput,
      totalOutput,
      avgInputPerRequest: totalInput / n,
      avgOutputPerRequest: totalOutput / n,
      costEstimate: cost,
      costPerHour,
    };
  }

  getToolStats() {
    const toolData = {};

    for (const req of this.requests) {
      for (const tool of req.toolsUsed) {
        const name = tool.name;
        if (!toolData[name]) {
          toolData[name] = { calls: 0, failures: 0, totalDuration: 0 };
        }
        toolData[name].calls++;
        if (!tool.success) toolData[name].failures++;
        toolData[name].totalDuration += tool.duration_ms || 0;
      }
    }

    const result = {};
    for (const [name, data] of Object.entries(toolData)) {
      result[name] = {
        calls: data.calls,
        failures: data.failures,
        failureRate: data.calls > 0 ? (data.failures / data.calls) * 100 : 0,
        avgDurationMs: data.calls > 0 ? data.totalDuration / data.calls : 0,
      };
    }
    return result;
  }

  getThroughput(windowMinutes = 5) {
    const cutoff = Date.now() - windowMinutes * 60 * 1000;
    const recent = this.requests.filter((r) => r.timestamp >= cutoff).length;
    return recent / windowMinutes;
  }

  reset() {
    this.requests = [];
    this.startTime = Date.now();
  }

  toDict() {
    return {
      requestCount: this.getRequestCount(),
      errorRate: this.getErrorRate(),
      latency: this.getLatencyPercentiles(),
      tokens: this.getTokenStats(),
      tools: this.getToolStats(),
      throughputRpm: this.getThroughput(),
      uptimeSeconds: (Date.now() - this.startTime) / 1000,
    };
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

export { MetricsCollector, SONNET_INPUT_COST_PER_MILLION, SONNET_OUTPUT_COST_PER_MILLION };

const isMain = process.argv[1] && process.argv[1].endsWith("metrics_collector.js");
if (isMain) {
  selfTest();
}
