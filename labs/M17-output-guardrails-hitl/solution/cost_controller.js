/**
 * M17: Cost Controller — Solution
 * Tracks token usage costs and enforces per-request budget limits.
 * Uses Claude Sonnet pricing: $3.00/1M input tokens, $15.00/1M output tokens.
 */

export class CostController {
  static COST_PER_INPUT_TOKEN = 3.00 / 1_000_000;
  static COST_PER_OUTPUT_TOKEN = 15.00 / 1_000_000;

  constructor(budgetLimit = 0.50) {
    this.budgetLimit = budgetLimit;
    this.currentCost = 0.0;
    this.callCount = 0;
    this.totalInputTokens = 0;
    this.totalOutputTokens = 0;
  }

  trackUsage(inputTokens, outputTokens) {
    const callCost =
      inputTokens * CostController.COST_PER_INPUT_TOKEN +
      outputTokens * CostController.COST_PER_OUTPUT_TOKEN;

    this.currentCost += callCost;
    this.callCount += 1;
    this.totalInputTokens += inputTokens;
    this.totalOutputTokens += outputTokens;

    const remaining = this.budgetLimit - this.currentCost;

    return {
      callCost: parseFloat(callCost.toFixed(6)),
      cumulativeCost: parseFloat(this.currentCost.toFixed(6)),
      budgetRemaining: parseFloat(remaining.toFixed(6)),
      budgetExceeded: this.currentCost > this.budgetLimit,
    };
  }

  checkBudget() {
    const remaining = this.budgetLimit - this.currentCost;
    const utilization = this.budgetLimit > 0
      ? (this.currentCost / this.budgetLimit) * 100
      : 0.0;

    return {
      currentCost: parseFloat(this.currentCost.toFixed(6)),
      budgetLimit: this.budgetLimit,
      budgetRemaining: parseFloat(remaining.toFixed(6)),
      budgetExceeded: this.currentCost > this.budgetLimit,
      utilizationPct: parseFloat(utilization.toFixed(1)),
    };
  }

  wouldExceed(estimatedInputTokens, estimatedOutputTokens) {
    const estimatedCost =
      estimatedInputTokens * CostController.COST_PER_INPUT_TOKEN +
      estimatedOutputTokens * CostController.COST_PER_OUTPUT_TOKEN;
    const budgetAfter = this.budgetLimit - this.currentCost - estimatedCost;

    return {
      estimatedCost: parseFloat(estimatedCost.toFixed(6)),
      wouldExceed: (this.currentCost + estimatedCost) > this.budgetLimit,
      budgetAfter: parseFloat(budgetAfter.toFixed(6)),
    };
  }

  reset() {
    this.currentCost = 0.0;
    this.callCount = 0;
    this.totalInputTokens = 0;
    this.totalOutputTokens = 0;
  }

  getSummary() {
    return {
      totalCost: parseFloat(this.currentCost.toFixed(6)),
      budgetLimit: this.budgetLimit,
      callCount: this.callCount,
      totalInputTokens: this.totalInputTokens,
      totalOutputTokens: this.totalOutputTokens,
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
  console.log("All tests complete.");
  console.log("=".repeat(60));
}
