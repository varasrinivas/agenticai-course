/**
 * M22 Lab — Cost Tracker (Starter)
 * =================================
 * Track every API call's cost, compare against baselines, and generate
 * a formatted report showing exactly where your money goes.
 *
 * KEY CONCEPT: You can't optimize what you don't measure. A cost tracker
 * turns vague "it seems expensive" into precise numbers.
 *
 * Usage:
 *     node cost_tracker.js
 */

const MODEL_PRICING = {
  "claude-3-5-haiku-20241022": { inputPer1m: 0.80, outputPer1m: 4.00 },
  "claude-sonnet-4": { inputPer1m: 3.00, outputPer1m: 15.00 },
  "claude-opus-4": { inputPer1m: 15.00, outputPer1m: 75.00 },
};

const BATCH_DISCOUNT = 0.5;

class CostTracker {
  constructor() {
    this.records = [];
    this.cacheSavings = 0.0;
  }

  /**
   * Calculate raw cost for a model call.
   * @param {string} model
   * @param {number} inputTokens
   * @param {number} outputTokens
   * @returns {number}
   */
  _calculateCost(model, inputTokens, outputTokens) {
    // TODO: Look up pricing and calculate cost
  }

  /**
   * Log an API call (or cache hit).
   * @param {string} model
   * @param {number} inputTokens
   * @param {number} outputTokens
   * @param {boolean} cached
   * @param {boolean} batch
   * @returns {object}
   */
  record(model, inputTokens, outputTokens, cached = false, batch = false) {
    // TODO: Implement cost recording
    // If cached: cost=0, add raw cost to cacheSavings
    // If batch: cost = rawCost * BATCH_DISCOUNT
    // Push record to this.records
  }

  /** @returns {number} Total actual cost */
  getTotalCost() {
    // TODO: Sum cost field
  }

  /** @returns {object} Breakdown by model */
  getCostByModel() {
    // TODO: Aggregate records by model
  }

  /** @returns {object} { cacheHits, cacheMisses, estimatedSavings } */
  getSavingsFromCache() {
    // TODO: Count cached vs non-cached records
  }

  /** @returns {object} { actualCost, baselineCost, savings, savingsPct } */
  getSavingsFromRouting() {
    // TODO: Compare actual cost vs all-Sonnet baseline
  }

  /** @returns {string} Formatted cost report */
  generateReport() {
    // TODO: Build formatted multi-line report
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

  // Seed-like reproducible random
  let seed = 42;
  function seededRandom() {
    seed = (seed * 16807 + 0) % 2147483647;
    return seed / 2147483647;
  }
  function randInt(min, max) {
    return Math.floor(seededRandom() * (max - min + 1)) + min;
  }

  const callScenarios = [
    ["claude-3-5-haiku-20241022", [400, 1000], [200, 500], 0.3, 0.1],
    ["claude-3-5-haiku-20241022", [500, 900], [150, 400], 0.4, 0.2],
    ["claude-sonnet-4", [800, 1500], [300, 800], 0.2, 0.05],
    ["claude-sonnet-4", [600, 1200], [200, 600], 0.25, 0.0],
    ["claude-opus-4", [1500, 3000], [500, 1500], 0.1, 0.0],
  ];

  for (let i = 0; i < 50; i++) {
    const scenario = callScenarios[i % callScenarios.length];
    const model = scenario[0];
    const inputTokens = randInt(...scenario[1]);
    const outputTokens = randInt(...scenario[2]);
    const cached = seededRandom() < scenario[3];
    const batch = seededRandom() < scenario[4];

    tracker.record(model, inputTokens, outputTokens, cached, batch);
  }

  console.log("\n--- Cost Report ---");
  const report = tracker.generateReport();
  console.log(report);

  const total = tracker.getTotalCost();
  const byModel = tracker.getCostByModel();
  const cacheInfo = tracker.getSavingsFromCache();
  const routingInfo = tracker.getSavingsFromRouting();

  console.log("\n--- Verification ---");
  console.log(`  Total cost: $${total.toFixed(4)}`);
  console.assert(total > 0, "FAIL: Total cost should be > 0");
  console.log("  PASS: Total cost is positive");

  console.log(`  Models used: ${Object.keys(byModel).join(", ")}`);
  console.assert(Object.keys(byModel).length >= 2, "FAIL: Should have multiple models");
  console.log("  PASS: Multiple models tracked");

  console.log(`  Cache hits: ${cacheInfo.cacheHits}, Savings: $${cacheInfo.estimatedSavings.toFixed(4)}`);
  console.assert(cacheInfo.cacheHits > 0, "FAIL: Should have cache hits");
  console.log("  PASS: Cache savings tracked");

  console.log(`  Routing savings: $${routingInfo.savings.toFixed(4)} (${routingInfo.savingsPct.toFixed(1)}%)`);
  console.assert(routingInfo.savings > 0, "FAIL: Routing should save vs all-Sonnet");
  console.log("  PASS: Routing savings tracked");

  console.log("\n" + "=".repeat(60));
  console.log("All cost tracker tests passed!");
  console.log("=".repeat(60));
}

selfTest();

export { CostTracker, MODEL_PRICING, BATCH_DISCOUNT };
