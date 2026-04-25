/**
 * M20 Lab — Monitoring: Drift Detector (Starter)
 * ===============================================
 * Build a drift detector that compares current metrics against a
 * saved baseline and flags significant changes.
 *
 * KEY CONCEPT: Threshold alerts catch sudden spikes. Drift detection
 * catches slow degradation — if latency creeps up 3% per day, no
 * single day triggers an alert, but after two weeks your p95 has
 * doubled. Drift detection compares current metrics to a known-good
 * baseline and flags anything that changed significantly (>20%).
 *
 * Usage:
 *     node drift_detector.js
 */

// =============================================================================
// DATA CLASSES
// =============================================================================

class DriftEvent {
  /**
   * @param {string} metricName
   * @param {number} baselineValue
   * @param {number} currentValue
   * @param {number} changePct
   * @param {boolean} isSignificant
   */
  constructor(metricName, baselineValue, currentValue, changePct, isSignificant) {
    this.metricName = metricName;
    this.baselineValue = baselineValue;
    this.currentValue = currentValue;
    this.changePct = changePct;
    this.isSignificant = isSignificant;
  }
}

// =============================================================================
// DRIFT DETECTOR
// =============================================================================

class DriftDetector {
  /**
   * @param {number} significanceThreshold - Percentage change that counts
   *   as significant (default 20.0 = >20% change triggers drift)
   */
  constructor(significanceThreshold = 20.0) {
    this.significanceThreshold = significanceThreshold;
    this.baseline = null;
    this.baselineTimestamp = null;
  }

  /**
   * Store a metrics snapshot as the baseline.
   * @param {Object} metrics - From MetricsCollector.toDict()
   */
  setBaseline(metrics) {
    // TODO: Deep copy the metrics and store as baseline
    // HINT: Use JSON.parse(JSON.stringify(metrics)) for deep copy
    // HINT: Also store Date.now() as baselineTimestamp
  }

  /**
   * Compare current metrics against the baseline.
   * @param {Object} currentMetrics
   * @returns {DriftEvent[]}
   */
  detectDrift(currentMetrics) {
    // TODO: If no baseline, return []
    //
    // Compare these metrics:
    // 1. errorRate (or error_rate) — direct comparison
    // 2. Latency percentiles — p50, p75, p90, p95, p99
    // 3. costPerHour (or cost_per_hour) from tokens
    // 4. throughputRpm (or throughput_rpm)
    // 5. Per-tool failure rates
    //
    // For each, call this._compareValues(name, baselineVal, currentVal)
    //
    // HINT: The metric keys may use camelCase (JS) or snake_case (Python dict)
    //   Support both by checking: metrics.errorRate ?? metrics.error_rate
  }

  /**
   * Compare two values and return a DriftEvent.
   * @param {string} name
   * @param {number} baselineVal
   * @param {number} currentVal
   * @returns {DriftEvent}
   */
  _compareValues(name, baselineVal, currentVal) {
    // TODO: Calculate changePct and isSignificant
    // HINT: If baselineVal === 0 and currentVal > 0: changePct = 100, significant
    // HINT: If both 0: changePct = 0, not significant
    // HINT: Otherwise: changePct = ((current - baseline) / baseline) * 100
    // HINT: isSignificant = Math.abs(changePct) > this.significanceThreshold
  }

  /**
   * Return only significant drift events.
   * @param {Object} currentMetrics
   * @returns {DriftEvent[]}
   */
  getSignificantDrifts(currentMetrics) {
    // TODO: Filter detectDrift() to only isSignificant === true
  }

  /** Check if a baseline has been set. */
  hasBaseline() {
    return this.baseline !== null;
  }
}

// =============================================================================
// DRIFT SIMULATION HELPER
// =============================================================================

/**
 * Artificially degrade metrics to test drift detection.
 * @param {Object} metrics
 * @param {number} degradationFactor - How much to degrade (1.5 = 50% worse)
 * @returns {Object} Degraded metrics
 */
function simulateDrift(metrics, degradationFactor = 1.5) {
  // TODO: Deep copy metrics and degrade key values
  // - Multiply errorRate by degradationFactor
  // - Multiply all latency percentiles by degradationFactor
  // - Multiply costPerHour by degradationFactor
  // - Divide throughputRpm by degradationFactor
  // - Increase tool failureRates by degradationFactor
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
  console.log(`\nBaseline set`);

  // Test 1: No drift
  const drifts = detector.getSignificantDrifts(baseline);
  console.log(`\nSame metrics -> ${drifts.length} significant drifts`);
  if (drifts.length !== 0) throw new Error("Expected no drift with identical metrics");
  console.log("  ✅ No drift with identical metrics — PASS");

  // Test 2: Simulated degradation
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
  if (significant.length < 2) throw new Error(`Expected >= 2 significant drifts, got ${significant.length}`);
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
