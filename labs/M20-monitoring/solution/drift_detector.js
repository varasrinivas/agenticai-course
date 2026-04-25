/**
 * M20 Lab — Monitoring: Drift Detector (Solution)
 * ================================================
 * Complete implementation of drift detection.
 *
 * Usage:
 *     node drift_detector.js
 */

class DriftEvent {
  constructor(metricName, baselineValue, currentValue, changePct, isSignificant) {
    this.metricName = metricName;
    this.baselineValue = baselineValue;
    this.currentValue = currentValue;
    this.changePct = changePct;
    this.isSignificant = isSignificant;
  }
}

class DriftDetector {
  constructor(significanceThreshold = 20.0) {
    this.significanceThreshold = significanceThreshold;
    this.baseline = null;
    this.baselineTimestamp = null;
  }

  setBaseline(metrics) {
    this.baseline = JSON.parse(JSON.stringify(metrics));
    this.baselineTimestamp = Date.now();
  }

  detectDrift(currentMetrics) {
    if (!this.baseline) return [];

    const events = [];

    // Helper to get values supporting both camelCase and snake_case
    const getVal = (obj, ...keys) => {
      for (const key of keys) {
        if (obj && obj[key] !== undefined) return obj[key];
      }
      return 0;
    };

    // 1. Error rate
    events.push(this._compareValues(
      "errorRate",
      getVal(this.baseline, "errorRate", "error_rate"),
      getVal(currentMetrics, "errorRate", "error_rate"),
    ));

    // 2. Latency percentiles
    const bLat = this.baseline.latency || {};
    const cLat = currentMetrics.latency || {};
    for (const p of ["p50", "p75", "p90", "p95", "p99"]) {
      events.push(this._compareValues(`latency_${p}`, bLat[p] || 0, cLat[p] || 0));
    }

    // 3. Cost per hour
    const bTokens = this.baseline.tokens || {};
    const cTokens = currentMetrics.tokens || {};
    events.push(this._compareValues(
      "costPerHour",
      getVal(bTokens, "costPerHour", "cost_per_hour"),
      getVal(cTokens, "costPerHour", "cost_per_hour"),
    ));

    // 4. Throughput
    events.push(this._compareValues(
      "throughputRpm",
      getVal(this.baseline, "throughputRpm", "throughput_rpm"),
      getVal(currentMetrics, "throughputRpm", "throughput_rpm"),
    ));

    // 5. Per-tool failure rates
    const bTools = this.baseline.tools || {};
    const cTools = currentMetrics.tools || {};
    const allToolNames = new Set([...Object.keys(bTools), ...Object.keys(cTools)]);
    for (const name of [...allToolNames].sort()) {
      const bRate = getVal(bTools[name] || {}, "failureRate", "failure_rate");
      const cRate = getVal(cTools[name] || {}, "failureRate", "failure_rate");
      events.push(this._compareValues(`tool_${name}_failureRate`, bRate, cRate));
    }

    return events;
  }

  _compareValues(name, baselineVal, currentVal) {
    let changePct, isSignificant;

    if (baselineVal === 0) {
      if (currentVal > 0) {
        changePct = 100.0;
        isSignificant = true;
      } else {
        changePct = 0.0;
        isSignificant = false;
      }
    } else {
      changePct = ((currentVal - baselineVal) / baselineVal) * 100.0;
      isSignificant = Math.abs(changePct) > this.significanceThreshold;
    }

    return new DriftEvent(name, baselineVal, currentVal, changePct, isSignificant);
  }

  getSignificantDrifts(currentMetrics) {
    return this.detectDrift(currentMetrics).filter((d) => d.isSignificant);
  }

  hasBaseline() {
    return this.baseline !== null;
  }
}

function simulateDrift(metrics, degradationFactor = 1.5) {
  const degraded = JSON.parse(JSON.stringify(metrics));

  // Error rate
  const errKey = "errorRate" in degraded ? "errorRate" : "error_rate";
  if (errKey in degraded) degraded[errKey] *= degradationFactor;

  // Latency
  if (degraded.latency) {
    for (const p of ["p50", "p75", "p90", "p95", "p99"]) {
      if (p in degraded.latency) degraded.latency[p] *= degradationFactor;
    }
  }

  // Cost
  if (degraded.tokens) {
    const cphKey = "costPerHour" in degraded.tokens ? "costPerHour" : "cost_per_hour";
    if (cphKey in degraded.tokens) degraded.tokens[cphKey] *= degradationFactor;
    const ceKey = "costEstimate" in degraded.tokens ? "costEstimate" : "cost_estimate";
    if (ceKey in degraded.tokens) degraded.tokens[ceKey] *= degradationFactor;
  }

  // Throughput
  const tKey = "throughputRpm" in degraded ? "throughputRpm" : "throughput_rpm";
  if (tKey in degraded) degraded[tKey] /= degradationFactor;

  // Tool failure rates
  if (degraded.tools) {
    for (const name of Object.keys(degraded.tools)) {
      const frKey = "failureRate" in degraded.tools[name] ? "failureRate" : "failure_rate";
      if (frKey in degraded.tools[name]) {
        degraded.tools[name][frKey] *= degradationFactor;
      }
    }
  }

  return degraded;
}

// =============================================================================
// SELF-TEST
// =============================================================================

function selfTest() {
  console.log("=".repeat(60));
  console.log("M20 Drift Detector — Self-Test");
  console.log("=".repeat(60));

  const detector = new DriftDetector(20.0);

  const baseline = {
    requestCount: 500,
    errorRate: 2.0,
    latency: { p50: 200, p75: 400, p90: 800, p95: 1500, p99: 3000 },
    tokens: { totalInput: 500000, totalOutput: 250000, costEstimate: 5.25, costPerHour: 0.5 },
    tools: {
      search_filings: { calls: 300, failures: 5, failureRate: 1.7, avgDurationMs: 45 },
      get_details: { calls: 200, failures: 2, failureRate: 1.0, avgDurationMs: 12 },
    },
    throughputRpm: 8.3,
    uptimeSeconds: 3600,
  };

  detector.setBaseline(baseline);
  console.log("\nBaseline set");

  // Test 1: No drift
  const drifts = detector.getSignificantDrifts(baseline);
  console.log(`\nSame metrics -> ${drifts.length} significant drifts`);
  if (drifts.length !== 0) throw new Error("Expected no drift");
  console.log("  ✅ No drift with identical metrics — PASS");

  // Test 2: Degradation
  const degraded = simulateDrift(baseline, 1.5);
  const allDrifts = detector.detectDrift(degraded);
  const significant = allDrifts.filter((d) => d.isSignificant);

  console.log(`\nDegraded (1.5x) -> ${significant.length} significant drifts out of ${allDrifts.length} total`);
  for (const d of significant) {
    const dir = d.changePct > 0 ? "↑" : "↓";
    console.log(
      `  ${dir} ${d.metricName}: ${d.baselineValue.toFixed(1)} -> ` +
      `${d.currentValue.toFixed(1)} (${d.changePct > 0 ? "+" : ""}${d.changePct.toFixed(1)}%)`
    );
  }
  if (significant.length < 2) throw new Error(`Expected >= 2 significant drifts`);
  console.log("  ✅ Drift detected after degradation — PASS");

  // Test 3: Minor change
  const minor = JSON.parse(JSON.stringify(baseline));
  minor.errorRate = 2.2;
  const minorDrifts = detector.getSignificantDrifts(minor);
  const errorDrifts = minorDrifts.filter((d) => d.metricName === "errorRate" || d.metricName === "error_rate");
  if (errorDrifts.length !== 0) throw new Error("10% change should not be significant");
  console.log("\n  ✅ Minor change (10%) correctly ignored — PASS");

  console.log(`\n${"=".repeat(60)}`);
  console.log("Self-test complete!");
  console.log("=".repeat(60));
}

export { DriftDetector, DriftEvent, simulateDrift };

const isMain = process.argv[1] && process.argv[1].endsWith("drift_detector.js");
if (isMain) {
  selfTest();
}
