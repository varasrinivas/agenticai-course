/**
 * M02 Lab — Step 2: Cost Estimator (Node.js Solution)
 * =====================================================
 * Predict API costs before making requests.
 */

// Pricing per million tokens (as of 2024)
const PRICING = {
  "claude-haiku": { input: 0.25, output: 1.25 },
  "claude-sonnet": { input: 3.0, output: 15.0 },
  "claude-opus": { input: 15.0, output: 75.0 },
};

/**
 * Estimate the cost of an API call.
 *
 * @param {number} inputTokens - Number of input tokens
 * @param {number} outputTokens - Number of output tokens
 * @param {string} model - Model key from PRICING
 * @returns {{ inputCost: number, outputCost: number, totalCost: number, model: string }}
 */
function estimateCost(inputTokens, outputTokens, model = "claude-sonnet") {
  const prices = PRICING[model];
  if (!prices) {
    throw new Error(`Unknown model: ${model}`);
  }
  const inputCost = (inputTokens / 1_000_000) * prices.input;
  const outputCost = (outputTokens / 1_000_000) * prices.output;
  return {
    inputCost,
    outputCost,
    totalCost: inputCost + outputCost,
    model,
  };
}

// ─── Main ───────────────────────────────────────────────────────────────────

console.log("=== Cost Estimator ===\n");

const scenarios = [
  ["Short query", 100, 200],
  ["Medium query", 1000, 2000],
  ["Batch of 1000", 1000 * 1000, 1000 * 2000],
];

for (const modelKey of ["claude-haiku", "claude-sonnet"]) {
  console.log(`Model: ${modelKey}`);
  for (const [label, inp, out] of scenarios) {
    try {
      const est = estimateCost(inp, out, modelKey);
      console.log(
        `  ${label.padEnd(18)} (${inp} in / ${out} out):   $${est.totalCost.toFixed(6)}`
      );
    } catch (e) {
      console.log(`  ${label.padEnd(18)} [ERROR] ${e.message}`);
    }
  }
  console.log();
}

// Cost comparison
try {
  const haiku = estimateCost(1000, 2000, "claude-haiku");
  const sonnet = estimateCost(1000, 2000, "claude-sonnet");
  const ratio = sonnet.totalCost / haiku.totalCost;
  console.log("Cost comparison:");
  console.log(
    `  Sonnet is ${ratio.toFixed(1)}x more expensive than Haiku for the same workload.`
  );
  const dailyHaiku = haiku.totalCost * 10000;
  const dailySonnet = sonnet.totalCost * 10000;
  console.log(
    `  For 10,000 queries/day, Haiku = $${dailyHaiku.toFixed(2)}/day, Sonnet = $${dailySonnet.toFixed(2)}/day.`
  );
} catch (e) {
  console.log(`  [ERROR] ${e.message}`);
}
