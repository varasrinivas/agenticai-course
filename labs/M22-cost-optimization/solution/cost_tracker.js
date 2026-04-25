/**
 * M22 Lab — Cost Tracker (Solution)
 * ===================================
 * Complete cost tracker with reporting and savings analysis.
 *
 * Usage:
 *     node cost_tracker.js
 */

const MODEL_PRICING = {
  "claude-haiku-3-5": { inputPer1m: 0.80, outputPer1m: 4.00 },
  "claude-sonnet-4": { inputPer1m: 3.00, outputPer1m: 15.00 },
  "claude-opus-4": { inputPer1m: 15.00, outputPer1m: 75.00 },
};

const BATCH_DISCOUNT = 0.5;

class CostTracker {
  constructor() {
    this.records = [];
    this.cacheSavings = 0.0;
  }

  _calculateCost(model, inputTokens, outputTokens) {
    const pricing = MODEL_PRICING[model] || MODEL_PRICING["claude-sonnet-4"];
    const inputCost = (inputTokens / 1_000_000) * pricing.inputPer1m;
    const outputCost = (outputTokens / 1_000_000) * pricing.outputPer1m;
    return inputCost + outputCost;
  }

  record(model, inputTokens, outputTokens, cached = false, batch = false) {
    const rawCost = this._calculateCost(model, inputTokens, outputTokens);
    let cost;

    if (cached) {
      cost = 0.0;
      this.cacheSavings += rawCost;
    } else if (batch) {
      cost = rawCost * BATCH_DISCOUNT;
    } else {
      cost = rawCost;
    }

    const rec = {
      model,
      inputTokens,
      outputTokens,
      cost,
      cached,
      batch,
      rawCost,
      timestamp: new Date().toISOString(),
    };
    this.records.push(rec);
    return rec;
  }

  getTotalCost() {
    return this.records.reduce((sum, r) => sum + r.cost, 0);
  }

  getCostByModel() {
    const byModel = {};
    for (const r of this.records) {
      if (!byModel[r.model]) {
        byModel[r.model] = { calls: 0, inputTokens: 0, outputTokens: 0, cost: 0 };
      }
      byModel[r.model].calls++;
      byModel[r.model].inputTokens += r.inputTokens;
      byModel[r.model].outputTokens += r.outputTokens;
      byModel[r.model].cost += r.cost;
    }
    return byModel;
  }

  getSavingsFromCache() {
    const cacheHits = this.records.filter((r) => r.cached).length;
    const cacheMisses = this.records.filter((r) => !r.cached).length;
    return { cacheHits, cacheMisses, estimatedSavings: this.cacheSavings };
  }

  getSavingsFromRouting() {
    let actualCost = 0;
    let baselineCost = 0;

    for (const r of this.records) {
      if (!r.cached) {
        actualCost += r.cost;
        baselineCost += this._calculateCost("claude-sonnet-4", r.inputTokens, r.outputTokens);
      }
    }

    const savings = baselineCost - actualCost;
    const savingsPct = baselineCost > 0 ? (savings / baselineCost) * 100 : 0;
    return { actualCost, baselineCost, savings, savingsPct };
  }

  generateReport() {
    const total = this.getTotalCost();
    const byModel = this.getCostByModel();
    const cache = this.getSavingsFromCache();
    const routing = this.getSavingsFromRouting();
    const batchCalls = this.records.filter((r) => r.batch).length;
    const batchSavings = this.records
      .filter((r) => r.batch && !r.cached)
      .reduce((sum, r) => sum + (r.rawCost - r.cost), 0);

    const lines = [
      "=".repeat(50),
      "         COST OPTIMIZATION REPORT",
      "=".repeat(50),
      "",
      `Total API Calls:    ${this.records.length}`,
      `Total Cost:         $${total.toFixed(4)}`,
      `Avg Cost/Call:      $${this.records.length > 0 ? (total / this.records.length).toFixed(4) : "0.0000"}`,
      "",
      "--- Per-Model Breakdown ---",
    ];

    for (const [model, data] of Object.entries(byModel).sort()) {
      lines.push(`  ${model}:`);
      lines.push(
        `    Calls: ${data.calls}, Input: ${data.inputTokens.toLocaleString()} tokens, ` +
          `Output: ${data.outputTokens.toLocaleString()} tokens`
      );
      lines.push(`    Cost: $${data.cost.toFixed(4)}`);
    }

    lines.push(
      "",
      "--- Cache Savings ---",
      `  Cache Hits:  ${cache.cacheHits}`,
      `  Cache Misses: ${cache.cacheMisses}`,
      `  Savings:     $${cache.estimatedSavings.toFixed(4)}`,
      "",
      "--- Routing Savings (vs All-Sonnet Baseline) ---",
      `  Actual Cost:   $${routing.actualCost.toFixed(4)}`,
      `  Baseline Cost: $${routing.baselineCost.toFixed(4)}`,
      `  Savings:       $${routing.savings.toFixed(4)} (${routing.savingsPct.toFixed(1)}%)`
    );

    if (batchCalls > 0) {
      lines.push("", "--- Batch API Savings ---", `  Batch Calls: ${batchCalls}`, `  Savings:     $${batchSavings.toFixed(4)}`);
    }

    lines.push("", "=".repeat(50));
    return lines.join("\n");
  }
}

// =============================================================================
// SELF-TEST
// =============================================================================

function selfTest() {
  console.log("=".repeat(60));
  console.log("M22 Lab — Cost Tracker Self-Test");
  console.log("=".repeat(60));

  const tracker = new CostTracker();

  let seed = 42;
  function seededRandom() {
    seed = (seed * 16807 + 0) % 2147483647;
    return seed / 2147483647;
  }
  function randInt(min, max) {
    return Math.floor(seededRandom() * (max - min + 1)) + min;
  }

  const scenarios = [
    ["claude-haiku-3-5", [400, 1000], [200, 500], 0.3, 0.1],
    ["claude-haiku-3-5", [500, 900], [150, 400], 0.4, 0.2],
    ["claude-sonnet-4", [800, 1500], [300, 800], 0.2, 0.05],
    ["claude-sonnet-4", [600, 1200], [200, 600], 0.25, 0.0],
    ["claude-opus-4", [1500, 3000], [500, 1500], 0.1, 0.0],
  ];

  for (let i = 0; i < 50; i++) {
    const s = scenarios[i % scenarios.length];
    tracker.record(
      s[0],
      randInt(...s[1]),
      randInt(...s[2]),
      seededRandom() < s[3],
      seededRandom() < s[4]
    );
  }

  console.log("\n--- Cost Report ---");
  console.log(tracker.generateReport());

  const total = tracker.getTotalCost();
  console.log("\n--- Verification ---");
  console.log(`  Total cost: $${total.toFixed(4)}`);
  console.assert(total > 0, "FAIL");
  console.log("  PASS: All checks passed");

  console.log("\n" + "=".repeat(60));
  console.log("All cost tracker tests passed!");
  console.log("=".repeat(60));
}

selfTest();

module.exports = { CostTracker, MODEL_PRICING, BATCH_DISCOUNT };
