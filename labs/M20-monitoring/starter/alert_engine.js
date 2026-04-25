/**
 * M20 Lab — Monitoring: Alert Engine (Starter)
 * =============================================
 * Build an alert engine that evaluates metrics against configurable
 * rules and fires alerts when thresholds are breached.
 *
 * KEY CONCEPT: Alerts are the bridge between metrics and action.
 * Without alerts, dashboards are just screensavers. A good alert
 * engine has severity levels so on-call engineers know what needs
 * immediate attention vs what can wait.
 *
 * Usage:
 *     node alert_engine.js
 */

// =============================================================================
// DATA CLASSES
// =============================================================================

class AlertRule {
  /**
   * @param {string} name - Human-readable rule name
   * @param {Function} conditionFn - Takes metrics object, returns boolean
   * @param {string} severity - "critical" | "warning" | "info"
   * @param {string} messageTemplate - Template with {value} placeholder
   * @param {Function} valueFn - Extracts the metric value for display
   */
  constructor(name, conditionFn, severity, messageTemplate, valueFn = null) {
    this.name = name;
    this.conditionFn = conditionFn;
    this.severity = severity;
    this.messageTemplate = messageTemplate;
    this.valueFn = valueFn;
  }
}

class Alert {
  /**
   * @param {string} ruleName
   * @param {string} severity
   * @param {string} message
   * @param {number} timestamp
   * @param {*} metricValue
   */
  constructor(ruleName, severity, message, timestamp, metricValue) {
    this.ruleName = ruleName;
    this.severity = severity;
    this.message = message;
    this.timestamp = timestamp;
    this.metricValue = metricValue;
  }
}

// =============================================================================
// ALERT ENGINE
// =============================================================================

class AlertEngine {
  constructor() {
    this.rules = [];
    this._setupDefaultRules();
  }

  _setupDefaultRules() {
    // TODO: Add 5 default rules using this.addRule()
    //
    // Rule 1: High error rate (>5% = critical)
    // - Check: metrics.errorRate > 5
    // - Message: "Error rate is {value}% (threshold: 5%)"
    //
    // Rule 2: High latency p95 (>10,000ms = warning)
    // - Check: metrics.latency.p95 > 10000
    // - Message: "P95 latency is {value}ms (threshold: 10,000ms)"
    //
    // Rule 3: High cost (>$1/hr = warning)
    // - Check: metrics.tokens.costPerHour > 1.0
    // - Message: "Cost rate is ${value}/hr (threshold: $1.00/hr)"
    //
    // Rule 4: Tool failure rate (any tool >10% = critical)
    // - Check: any tool in metrics.tools has failureRate > 10
    // - Message: "Tool failure rate is {value}% (threshold: 10%)"
    //
    // Rule 5: Stale (no requests for 5+ min = info)
    // - Check: metrics.throughputRpm === 0 && metrics.uptimeSeconds > 300
    // - Message: "No requests in last 5 minutes (uptime: {value}s)"
    //
    // HINT: Wrap condition checks in try/catch for robustness
  }

  /** Register a new alert rule. */
  addRule(rule) {
    // TODO: Push rule to this.rules
  }

  /**
   * Evaluate all rules against the given metrics.
   *
   * @param {Object} metrics - From MetricsCollector.toDict()
   * @returns {Alert[]} Triggered alerts
   */
  evaluate(metrics) {
    // TODO: Iterate through this.rules
    // For each rule that triggers:
    //   1. Extract metric value via rule.valueFn
    //   2. Format message by replacing {value}
    //   3. Create Alert object
    // HINT: Wrap each rule in try/catch
  }
}

// =============================================================================
// SELF-TEST
// =============================================================================

function selfTest() {
  console.log("=".repeat(60));
  console.log("M20 Alert Engine — Self-Test");
  console.log("=".repeat(60));

  const engine = new AlertEngine();

  // Test 1: Healthy metrics
  const healthyMetrics = {
    requestCount: 500,
    errorRate: 1.2,
    latency: { p50: 200, p75: 400, p90: 800, p95: 1500, p99: 3000 },
    tokens: { totalInput: 500000, totalOutput: 250000, costEstimate: 0.5, costPerHour: 0.25 },
    tools: {
      search_filings: { calls: 300, failures: 5, failureRate: 1.7, avgDurationMs: 45 },
      get_details: { calls: 200, failures: 2, failureRate: 1.0, avgDurationMs: 12 },
    },
    throughputRpm: 8.3,
    uptimeSeconds: 3600,
  };

  let alerts = engine.evaluate(healthyMetrics);
  console.log(`\nHealthy metrics -> ${alerts.length} alerts`);
  if (alerts.length !== 0) throw new Error(`Expected 0 alerts, got ${alerts.length}`);
  console.log("  ✅ No alerts — PASS");

  // Test 2: Degraded metrics
  const degradedMetrics = {
    requestCount: 500,
    errorRate: 8.5,
    latency: { p50: 2000, p75: 5000, p90: 9000, p95: 12000, p99: 18000 },
    tokens: { totalInput: 5000000, totalOutput: 2500000, costEstimate: 52.5, costPerHour: 2.1 },
    tools: {
      search_filings: { calls: 300, failures: 45, failureRate: 15.0, avgDurationMs: 145 },
      get_details: { calls: 200, failures: 2, failureRate: 1.0, avgDurationMs: 12 },
    },
    throughputRpm: 8.3,
    uptimeSeconds: 3600,
  };

  alerts = engine.evaluate(degradedMetrics);
  console.log(`\nDegraded metrics -> ${alerts.length} alerts`);
  const icons = { critical: "🔴", warning: "🟡", info: "🔵" };
  for (const alert of alerts) {
    console.log(`  ${icons[alert.severity]} [${alert.severity.toUpperCase()}] ${alert.ruleName}: ${alert.message}`);
  }
  if (alerts.length < 3) throw new Error(`Expected >= 3 alerts, got ${alerts.length}`);
  if (!alerts.some((a) => a.severity === "critical")) throw new Error("Expected critical alert");
  console.log("  ✅ Multiple alerts with correct severities — PASS");

  // Test 3: Stale metrics
  const staleMetrics = {
    requestCount: 0,
    errorRate: 0,
    latency: { p50: 0, p75: 0, p90: 0, p95: 0, p99: 0 },
    tokens: { totalInput: 0, totalOutput: 0, costEstimate: 0, costPerHour: 0 },
    tools: {},
    throughputRpm: 0,
    uptimeSeconds: 600,
  };

  alerts = engine.evaluate(staleMetrics);
  console.log(`\nStale metrics -> ${alerts.length} alerts`);
  for (const alert of alerts) {
    console.log(`  ${icons[alert.severity]} [${alert.severity.toUpperCase()}] ${alert.ruleName}: ${alert.message}`);
  }
  const staleAlerts = alerts.filter((a) => a.ruleName === "stale_no_requests");
  if (staleAlerts.length < 1) throw new Error("Expected stale alert");
  console.log("  ✅ Stale detection works — PASS");

  console.log(`\n${"=".repeat(60)}`);
  console.log("Self-test complete!");
  console.log("=".repeat(60));
}

export { AlertEngine, AlertRule, Alert };

const isMain = process.argv[1] && process.argv[1].endsWith("alert_engine.js");
if (isMain) {
  selfTest();
}
