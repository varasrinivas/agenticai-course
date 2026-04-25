/**
 * M20 Lab — Monitoring: Dashboard (Starter)
 * ==========================================
 * Build a terminal-based ASCII monitoring dashboard that ties
 * together the metrics collector, alert engine, and drift detector.
 *
 * KEY CONCEPT: A dashboard is the "single pane of glass" for your
 * agent's health. It must answer three questions in under 5 seconds:
 * (1) Is the system up? (2) Is it healthy? (3) What changed recently?
 *
 * Usage:
 *     node dashboard.js
 */

import { MetricsCollector } from "./metrics_collector.js";
import { AlertEngine } from "./alert_engine.js";
import { DriftDetector } from "./drift_detector.js";

// =============================================================================
// TRAFFIC SIMULATOR
// =============================================================================

/**
 * Generate simulated traffic with realistic distributions.
 *
 * @param {MetricsCollector} collector
 * @param {number} numRequests
 * @param {number} errorRate - Fraction 0.0 to 1.0
 * @param {number} slowPct - Fraction of slow requests
 * @param {number} verySlowPct - Fraction of very slow requests
 */
function generateTraffic(
  collector,
  numRequests = 200,
  errorRate = 0.03,
  slowPct = 0.10,
  verySlowPct = 0.02
) {
  // TODO: Generate numRequests simulated requests
  //
  // For each request:
  // 1. Duration: verySlowPct chance of 5000-15000ms,
  //              slowPct chance of 1000-5000ms,
  //              otherwise 80-600ms
  // 2. Success: Math.random() >= errorRate
  // 3. Tokens: input 400-2500, output 150-1800
  // 4. Tools: 1-3 random tools from ["search_filings", "get_details", "calc_risk"]
  // 5. Record via collector.recordRequest()
}

// =============================================================================
// DASHBOARD RENDERER
// =============================================================================

class Dashboard {
  /**
   * @param {MetricsCollector} metricsCollector
   * @param {AlertEngine} alertEngine
   * @param {DriftDetector} driftDetector
   */
  constructor(metricsCollector, alertEngine, driftDetector) {
    this.collector = metricsCollector;
    this.alerts = alertEngine;
    this.drift = driftDetector;
    this.WIDTH = 62;
  }

  /**
   * Render the dashboard as a string and print it.
   * @returns {string} The rendered dashboard
   */
  render() {
    // TODO: Build the ASCII dashboard string
    //
    // Layout (box-drawing characters):
    // 1. Title bar
    // 2. Summary: requests, error rate, uptime
    // 3. Latency: p50, p75, p90, p95, p99
    // 4. Cost: total, rate/hr, avg/req
    // 5. Tokens: total input, total output
    // 6. Tools: per-tool stats
    // 7. Alerts: active alerts or "No active alerts"
    // 8. Drift: drift events or "No significant drift"
    //
    // Use: ╔ ═ ╗ ║ ╠ ╣ ╚ ╝
    //
    // HINT: Get metrics via this.collector.toDict()
    // HINT: Get alerts via this.alerts.evaluate(metrics)
    // HINT: Get drifts via this.drift.getSignificantDrifts(metrics)
    // HINT: Use helper methods for formatting
  }

  /**
   * Format seconds into uptime string.
   * @param {number} seconds
   * @returns {string}
   */
  _formatUptime(seconds) {
    // TODO: Convert to "Xh Ym" or "Xm Ys"
  }
}

// =============================================================================
// MAIN
// =============================================================================

function main() {
  console.log("=".repeat(62));
  console.log("  M20 Monitoring Dashboard — Full Integration Demo");
  console.log("=".repeat(62));

  // TODO: Implement full integration
  //
  // Step 1: Create components
  //   const collector = new MetricsCollector();
  //   const alertEngine = new AlertEngine();
  //   const driftDetector = new DriftDetector();
  //   const dashboard = new Dashboard(collector, alertEngine, driftDetector);
  //
  // Step 2: Generate 200 normal requests (3% error, 10% slow)
  //   generateTraffic(collector, 200, 0.03, 0.10, 0.02);
  //
  // Step 3: Set baseline
  //   driftDetector.setBaseline(collector.toDict());
  //
  // Step 4: Render normal dashboard
  //   console.log("\n>>> DASHBOARD — Normal Traffic");
  //   dashboard.render();
  //
  // Step 5: Generate 50 degraded requests (25% error, 40% slow, 15% very slow)
  //   generateTraffic(collector, 50, 0.25, 0.40, 0.15);
  //
  // Step 6: Render degraded dashboard
  //   console.log("\n>>> DASHBOARD — After Degradation");
  //   dashboard.render();
}

export { Dashboard, generateTraffic };

const isMain = process.argv[1] && process.argv[1].endsWith("dashboard.js");
if (isMain) {
  main();
}
