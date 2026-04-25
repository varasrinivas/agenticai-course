/**
 * M17: Cost Controller — Starter
 * Tracks token usage costs and enforces per-request budget limits.
 * Uses Claude Sonnet pricing: $3.00/1M input tokens, $15.00/1M output tokens.
 */

export class CostController {
  // Claude Sonnet pricing (per token)
  static COST_PER_INPUT_TOKEN = 3.00 / 1_000_000;   // $3.00 per 1M input tokens
  static COST_PER_OUTPUT_TOKEN = 15.00 / 1_000_000;  // $15.00 per 1M output tokens

  /**
   * @param {number} budgetLimit - Maximum allowed cost per request in dollars (default $0.50).
   */
  constructor(budgetLimit = 0.50) {
    this.budgetLimit = budgetLimit;
    // TODO 1: Initialize tracking state:
    //   this.currentCost = 0.0;
    //   this.callCount = 0;
    //   this.totalInputTokens = 0;
    //   this.totalOutputTokens = 0;
  }

  /**
   * Record token usage from an API call and update running cost.
   * @param {number} inputTokens
   * @param {number} outputTokens
   * @returns {{ callCost: number, cumulativeCost: number, budgetRemaining: number, budgetExceeded: boolean }}
   */
  trackUsage(inputTokens, outputTokens) {
    // TODO 2: Calculate the cost of this call using COST_PER_INPUT_TOKEN
    // and COST_PER_OUTPUT_TOKEN. Update currentCost, callCount,
    // totalInputTokens, totalOutputTokens.
    const callCost = 0.0;

    return {
      callCost: parseFloat(callCost.toFixed(6)),
      cumulativeCost: parseFloat((0.0).toFixed(6)),
      budgetRemaining: parseFloat(this.budgetLimit.toFixed(6)),
      budgetExceeded: false,
    };
  }

  /**
   * Check current budget status.
   * @returns {{ currentCost: number, budgetLimit: number, budgetRemaining: number, budgetExceeded: boolean, utilizationPct: number }}
   */
  checkBudget() {
    // TODO 3: Calculate remaining budget and utilization percentage.
    return {
      currentCost: 0.0,
      budgetLimit: this.budgetLimit,
      budgetRemaining: this.budgetLimit,
      budgetExceeded: false,
      utilizationPct: 0.0,
    };
  }

  /**
   * Pre-check: would a call with these token counts exceed the budget?
   * @param {number} estimatedInputTokens
   * @param {number} estimatedOutputTokens
   * @returns {{ estimatedCost: number, wouldExceed: boolean, budgetAfter: number }}
   */
  wouldExceed(estimatedInputTokens, estimatedOutputTokens) {
    // TODO 4: Calculate the estimated cost and check if currentCost + estimated
    // would exceed budgetLimit.
    const estimatedCost = 0.0;

    return {
      estimatedCost: parseFloat(estimatedCost.toFixed(6)),
      wouldExceed: false,
      budgetAfter: parseFloat(this.budgetLimit.toFixed(6)),
    };
  }

  /** Reset all counters for a new request. */
  reset() {
    // TODO 5: Reset currentCost, callCount, totalInputTokens,
    // totalOutputTokens to zero.
  }

  /** Return a summary of all usage tracking. */
  getSummary() {
    return {
      totalCost: parseFloat((this.currentCost || 0).toFixed(6)),
      budgetLimit: this.budgetLimit,
      callCount: this.callCount || 0,
      totalInputTokens: this.totalInputTokens || 0,
      totalOutputTokens: this.totalOutputTokens || 0,
    };
  }
}

// ── Self-Test ───────────────────────────────────────────────
const isMain = process.argv[1] && (
  process.argv[1].endsWith("cost_controller.js") ||
  process.argv[1].endsWith("cost_controller.mjs")
);

if (isMain) {
  console.log("=".repeat(60));
  console.log("M17 Cost Controller — Self-Test");
  console.log("=".repeat(60));

  const controller = new CostController(0.50);

  const calls = [
    [1000, 500],
    [5000, 2000],
    [10000, 5000],
    [20000, 8000],
    [50000, 20000],
  ];

  for (let i = 0; i < calls.length; i++) {
    const [inp, out] = calls[i];
    const pre = controller.wouldExceed(inp, out);
    console.log(`\nCall ${i + 1}: ${inp} input + ${out} output tokens`);
    console.log(`  Pre-check — estimated cost: $${pre.estimatedCost.toFixed(6)}, would exceed: ${pre.wouldExceed}`);

    if (pre.wouldExceed) {
      console.log(`  BLOCKED — would exceed budget ($${pre.budgetAfter.toFixed(6)} remaining after)`);
      continue;
    }

    const result = controller.trackUsage(inp, out);
    console.log(`  Call cost: $${result.callCost.toFixed(6)}`);
    console.log(`  Cumulative: $${result.cumulativeCost.toFixed(6)}`);
    console.log(`  Remaining: $${result.budgetRemaining.toFixed(6)}`);
    console.log(`  Exceeded: ${result.budgetExceeded}`);
  }

  const budget = controller.checkBudget();
  console.log(`\n${"=".repeat(60)}`);
  console.log("Budget Summary:");
  console.log(`  Total cost: $${budget.currentCost.toFixed(6)}`);
  console.log(`  Budget limit: $${budget.budgetLimit.toFixed(2)}`);
  console.log(`  Utilization: ${budget.utilizationPct.toFixed(1)}%`);
  console.log(`  Exceeded: ${budget.budgetExceeded}`);

  console.log("\n" + "=".repeat(60));
  console.log("Self-test complete. Fill in TODOs to see correct cost tracking.");
  console.log("=".repeat(60));
}
