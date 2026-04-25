/**
 * M20 Lab — Monitoring: Alert Engine (Solution)
 * ==============================================
 * Complete implementation of the alert engine.
 *
 * Usage:
 *     node alert_engine.js
 */

class AlertRule {
  constructor(name, conditionFn, severity, messageTemplate, valueFn = null) {
    this.name = name;
    this.conditionFn = conditionFn;
    this.severity = severity;
    this.messageTemplate = messageTemplate;
    this.valueFn = valueFn;
  }
}

class Alert {
  constructor(ruleName, severity, message, timestamp, metricValue) {
    this.ruleName = ruleName;
    this.severity = severity;
    this.message = message;
    this.timestamp = timestamp;
    this.metricValue = metricValue;
  }
}

class AlertEngine {
  constructor() {
    this.rules = [];
    this._setupDefaultRules();
  }

  _setupDefaultRules() {
    // Rule 1: High error rate
    this.addRule(new AlertRule(
      "high_error_rate",
      (m) => { try { return (m.errorRate ?? m.error_rate ?? 0) > 5; } catch { return false; } },
      "critical",
      "Error rate is {value}% (threshold: 5%)",
      (m) => (m.errorRate ?? m.error_rate ?? 0).toFixed(1),
    ));

    // Rule 2: High latency p95
    this.addRule(new AlertRule(
      "high_latency_p95",
      (m) => { try { return (m.latency?.p95 ?? 0) > 10000; } catch { return false; } },
      "warning",
      "P95 latency is {value}ms (threshold: 10,000ms)",
      (m) => Math.round(m.latency?.p95 ?? 0),
    ));

    // Rule 3: High cost
    this.addRule(new AlertRule(
      "high_cost",
      (m) => {
        try {
          const cph = m.tokens?.costPerHour ?? m.tokens?.cost_per_hour ?? 0;
          return cph > 1.0;
        } catch { return false; }
      },
      "warning",
      "Cost rate is ${value}/hr (threshold: $1.00/hr)",
      (m) => (m.tokens?.costPerHour ?? m.tokens?.cost_per_hour ?? 0).toFixed(2),
    ));

    // Rule 4: Tool failure rate
    this.addRule(new AlertRule(
      "tool_failure_rate",
      (m) => {
        try {
          const tools = m.tools ?? {};
          for (const stats of Object.values(tools)) {
            if ((stats.failureRate ?? stats.failure_rate ?? 0) > 10) return true;
          }
          return false;
        } catch { return false; }
      },
      "critical",
      "Tool failure rate is {value}% (threshold: 10%)",
      (m) => {
        let max = 0;
        for (const stats of Object.values(m.tools ?? {})) {
          const rate = stats.failureRate ?? stats.failure_rate ?? 0;
          if (rate > max) max = rate;
        }
        return max.toFixed(1);
      },
    ));

    // Rule 5: Stale
    this.addRule(new AlertRule(
      "stale_no_requests",
      (m) => {
        try {
          const rpm = m.throughputRpm ?? m.throughput_rpm ?? 0;
          const uptime = m.uptimeSeconds ?? m.uptime_seconds ?? 0;
          return rpm === 0 && uptime > 300;
        } catch { return false; }
      },
      "info",
      "No requests in last 5 minutes (uptime: {value}s)",
      (m) => Math.round(m.uptimeSeconds ?? m.uptime_seconds ?? 0),
    ));
  }

  addRule(rule) {
    this.rules.push(rule);
  }

  evaluate(metrics) {
    const triggered = [];

    for (const rule of this.rules) {
      try {
        if (rule.conditionFn(metrics)) {
          const value = rule.valueFn ? rule.valueFn(metrics) : null;
          const message = value !== null
            ? rule.messageTemplate.replace("{value}", value)
            : rule.messageTemplate;
          triggered.push(new Alert(
            rule.name,
            rule.severity,
            message,
            Date.now(),
            value,
          ));
        }
      } catch {
        // Skip bad rules
      }
    }

    return triggered;
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
