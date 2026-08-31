const assert = require("node:assert/strict");
/**
 * M20 Lab - Step 1: Z-Score Drift Detector (Node.js)
 * ===================================================
 * Pure algorithm — no LLM, no infrastructure. Run: node drift_detector.js
 */

// (COMPLETE) helpers
const mean = (arr) => arr.reduce((a, b) => a + b, 0) / arr.length;
const stddev = (arr) => {
  const m = mean(arr);
  return Math.sqrt(arr.reduce((s, v) => s + (v - m) ** 2, 0) / arr.length);
};

class RollingWindow {
  constructor(maxSize) {
    this.maxSize = maxSize;
    this.data = [];
  }
  push(val) {
    this.data.push(val);
    if (this.data.length > this.maxSize) this.data.shift();
  }
  get values() {
    return [...this.data];
  }
  get size() {
    return this.data.length;
  }
}

class DriftDetector {
  static MIN_SAMPLES = 30; // small samples scream false alarms

  constructor(windowSize = 2016) { // 7 days at 5-min resolution
    this.qualityW = new RollingWindow(windowSize);
    this.tokensW = new RollingWindow(windowSize);
    this.toolFreqW = new RollingWindow(windowSize);
  }

  /** (COMPLETE) Push samples, check all three metrics. */
  record(qualityScore, tokensUsed, toolCallsMade, maxToolCalls = 5) {
    this.qualityW.push(qualityScore);
    this.tokensW.push(tokensUsed);
    this.toolFreqW.push(toolCallsMade / Math.max(maxToolCalls, 1));

    return [
      this.checkDrift("quality_score", this.qualityW),
      this.checkDrift("tokens_per_query", this.tokensW),
      this.checkDrift("tool_call_frequency", this.toolFreqW),
    ].filter(Boolean);
  }

  /**
   * Z-score the LATEST sample against the rest of the window.
   *
   * TODO:
   * 1. If window.size < DriftDetector.MIN_SAMPLES: return null
   * 2. const values = window.values;
   *    const current = values[values.length - 1];
   *    const history = values.slice(0, -1);   ← EXCLUDING the latest
   * 3. const m = mean(history); const s = stddev(history);
   * 4. If s === 0: return null (constant history — skip)
   * 5. const z = (current - m) / s;
   * 6. If Math.abs(z) < 2: return null
   * 7. Return { metric, currentValue: current, baselineMean: m,
   *    baselineStd: s, zScore: z, direction: z > 0 ? "up" : "down",
   *    severity: Math.abs(z) >= 3 ? "critical" : "warning" }
   */
  checkDrift(metric, window) {
    // TODO: implement
  }
}

// ── Test harness (COMPLETE) ──
// Simple seeded PRNG so runs are reproducible
let seed = 9;
const rand = () => ((seed = (seed * 1103515245 + 12345) % 2 ** 31) / 2 ** 31);
const gauss = (mu, sigma) => {
  const u1 = Math.max(rand(), 1e-9), u2 = rand();
  return mu + sigma * Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
};

const det = new DriftDetector(200);

console.log("Phase 1: 60 samples of STABLE behavior");
let stableWarnings = 0;
let stableCriticals = 0;
for (let i = 0; i < 60; i++) {
  for (const a of det.record(gauss(0.85, 0.03), gauss(900, 60), [1, 2, 2, 3][i % 4])) {
    if (a.severity === "warning") stableWarnings++;
    else stableCriticals++;
  }
}
console.log(`  Stable phase: ${stableWarnings} warnings, ${stableCriticals} criticals`);
console.log("  (A handful of 2-sigma warnings is EXPECTED — |z|>=2 fires ~5% of");
console.log("   the time by pure chance. That's why only CRITICAL pages a human.)");

console.log("\nPhase 2: DEGRADED behavior (quality tanks, tokens triple)");
const fired = [];
for (let i = 0; i < 5; i++) {
  for (const a of det.record(0.55, 2800, 5)) {
    fired.push(a);
    console.log(`  [${a.severity.toUpperCase()}] ${a.metric}: ${a.currentValue.toFixed(2)} ` +
      `vs baseline ${a.baselineMean.toFixed(2)} +/- ${a.baselineStd.toFixed(2)} ` +
      `(z=${a.zScore >= 0 ? "+" : ""}${a.zScore.toFixed(1)}, ${a.direction})`);
  }
}

assert.ok(stableCriticals === 0, `criticals during stable phase: ${stableCriticals}`);
assert.ok(fired.some((a) => a.metric === "quality_score" && a.direction === "down" && a.severity === "critical"), "quality drop not critical");
assert.ok(fired.some((a) => a.metric === "tokens_per_query" && a.direction === "up" && a.severity === "critical"), "token explosion not critical");
console.log("\nAll drift checks passed.");
