/**
 * M20 Lab — Monitoring: Dashboard (Solution)
 * ===========================================
 * Complete implementation of the terminal-based ASCII dashboard.
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

function generateTraffic(
  collector,
  numRequests = 200,
  errorRate = 0.03,
  slowPct = 0.10,
  verySlowPct = 0.02
) {
  const toolNames = ["search_filings", "get_details", "calc_risk"];

  for (let i = 0; i < numRequests; i++) {
    let duration;
    const roll = Math.random();
    if (roll < verySlowPct) {
      duration = 5000 + Math.random() * 10000;
    } else if (roll < verySlowPct + slowPct) {
      duration = 1000 + Math.random() * 4000;
    } else {
      duration = 80 + Math.random() * 520;
    }

    const success = Math.random() >= errorRate;
    const inputTokens = Math.floor(400 + Math.random() * 2100);
    const outputTokens = Math.floor(150 + Math.random() * 1650);

    const numTools = 1 + Math.floor(Math.random() * 3);
    const tools = [];
    for (let j = 0; j < numTools; j++) {
      tools.push({
        name: toolNames[Math.floor(Math.random() * toolNames.length)],
        duration_ms: 5 + Math.random() * 115,
        success: Math.random() > 0.03,
      });
    }

    collector.recordRequest(duration, inputTokens, outputTokens, success, tools);
  }
}

// =============================================================================
// DASHBOARD RENDERER
// =============================================================================

class Dashboard {
  constructor(metricsCollector, alertEngine, driftDetector) {
    this.collector = metricsCollector;
    this.alerts = alertEngine;
    this.drift = driftDetector;
    this.WIDTH = 62;
  }

  render() {
    const metrics = this.collector.toDict();
    const alerts = this.alerts.evaluate(metrics);
    const drifts = this.drift.hasBaseline()
      ? this.drift.getSignificantDrifts(metrics)
      : [];

    const lines = [];
    const inner = this.WIDTH - 4; // space between "║ " and " ║"

    const top = () => lines.push("╔" + "═".repeat(this.WIDTH - 2) + "╗");
    const bottom = () => lines.push("╚" + "═".repeat(this.WIDTH - 2) + "╝");
    const separator = () => lines.push("╠" + "═".repeat(this.WIDTH - 2) + "╣");
    const row = (text) => {
      const display = text.substring(0, inner);
      lines.push("║ " + display.padEnd(inner) + " ║");
    };
    const sectionHeader = (text) => { separator(); row(text); };

    // Title
    top();
    const title = "UCC Agent Monitoring Dashboard";
    row(title.padStart(Math.floor((inner + title.length) / 2)).padEnd(inner));

    // Summary
    separator();
    const uptimeStr = this._formatUptime(metrics.uptimeSeconds || 0);
    const reqCount = (metrics.requestCount || 0).toLocaleString();
    const errRate = (metrics.errorRate || 0).toFixed(1);
    row(`Requests: ${reqCount}    Error Rate: ${errRate}%    Uptime: ${uptimeStr}`);

    // Latency
    sectionHeader("Latency (ms)");
    const lat = metrics.latency || {};
    row(
      `  p50: ${this._fmt(lat.p50)}  ` +
      `p75: ${this._fmt(lat.p75)}  ` +
      `p90: ${this._fmt(lat.p90)}  ` +
      `p95: ${this._fmt(lat.p95)}  ` +
      `p99: ${this._fmt(lat.p99)}`
    );

    // Cost
    sectionHeader("Cost");
    const tokens = metrics.tokens || {};
    const totalCost = tokens.costEstimate || 0;
    const costHr = tokens.costPerHour || 0;
    const reqCountNum = metrics.requestCount || 0;
    const avgCost = reqCountNum > 0 ? totalCost / reqCountNum : 0;
    row(`  Total: $${totalCost.toFixed(2)}    Rate: $${costHr.toFixed(2)}/hr    Avg: $${avgCost.toFixed(4)}/req`);

    // Tokens
    sectionHeader("Tokens");
    row(`  Input: ${(tokens.totalInput || 0).toLocaleString()}    Output: ${(tokens.totalOutput || 0).toLocaleString()}`);

    // Tools
    sectionHeader("Tools");
    const toolStats = metrics.tools || {};
    const toolNames = Object.keys(toolStats).sort();
    if (toolNames.length > 0) {
      for (const name of toolNames) {
        const s = toolStats[name];
        const calls = Math.round(s.calls || 0);
        const failRate = (s.failureRate || s.failure_rate || 0).toFixed(1);
        const avgDur = Math.round(s.avgDurationMs || s.avg_duration_ms || 0);
        row(`  ${name}:  ${calls} calls, ${failRate}% fail, avg ${avgDur}ms`);
      }
    } else {
      row("  No tool data");
    }

    // Alerts
    sectionHeader("Alerts");
    if (alerts.length > 0) {
      const icons = { critical: "🔴", warning: "🟡", info: "🔵" };
      for (const alert of alerts) {
        row(`  ${icons[alert.severity] || "⚪"} [${alert.severity.toUpperCase()}] ${alert.message}`);
      }
    } else {
      row("  ✅ No active alerts");
    }

    // Drift
    sectionHeader("Drift");
    if (drifts.length > 0) {
      for (const d of drifts) {
        const dir = d.changePct > 0 ? "↑" : "↓";
        row(
          `  ${dir} ${d.metricName}: ` +
          `${d.baselineValue.toFixed(1)} -> ${d.currentValue.toFixed(1)} ` +
          `(${d.changePct > 0 ? "+" : ""}${d.changePct.toFixed(1)}%)`
        );
      }
    } else {
      row("  ✅ No significant drift detected");
    }

    bottom();

    const output = lines.join("\n");
    console.log(output);
    return output;
  }

  _formatUptime(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (hours > 0) return `${hours}h ${minutes}m`;
    const secs = Math.floor(seconds % 60);
    return `${minutes}m ${secs}s`;
  }

  _fmt(val) {
    return Math.round(val || 0).toLocaleString();
  }
}

// =============================================================================
// MAIN
// =============================================================================

function main() {
  console.log("=".repeat(62));
  console.log("  M20 Monitoring Dashboard — Full Integration Demo");
  console.log("=".repeat(62));

  const collector = new MetricsCollector();
  const alertEngine = new AlertEngine();
  const driftDetector = new DriftDetector();
  const dashboard = new Dashboard(collector, alertEngine, driftDetector);

  // Normal traffic
  console.log("\nGenerating 200 normal requests...");
  generateTraffic(collector, 200, 0.03, 0.10, 0.02);

  driftDetector.setBaseline(collector.toDict());

  console.log("\n>>> DASHBOARD — Normal Traffic");
  dashboard.render();

  // Degraded traffic
  console.log("\n\nGenerating 50 degraded requests (25% errors, 40% slow)...");
  generateTraffic(collector, 50, 0.25, 0.40, 0.15);

  console.log("\n>>> DASHBOARD — After Degradation");
  dashboard.render();
}

export { Dashboard, generateTraffic };

const isMain = process.argv[1] && process.argv[1].endsWith("dashboard.js");
if (isMain) {
  main();
}
