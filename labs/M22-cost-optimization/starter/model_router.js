/**
 * M22 Lab — Model Router (Starter)
 * =================================
 * Route queries to the cheapest Claude model that can handle the task.
 * Filing lookups go to Haiku, entity resolution to Sonnet, and complex
 * risk analysis to Opus.
 *
 * KEY CONCEPT: Not every query needs the most powerful model. A simple
 * "look up filing #12345" costs 60x more on Opus than on Haiku, with
 * identical results. Routing by complexity is free money.
 *
 * Usage:
 *     node model_router.js
 */

const MODEL_PRICING = {
  "claude-3-5-haiku-20241022": {
    name: "claude-3-5-haiku-20241022",
    displayName: "Haiku 3.5",
    inputPer1m: 0.80,
    outputPer1m: 4.00,
  },
  "claude-sonnet-4": {
    name: "claude-sonnet-4",
    displayName: "Sonnet 4",
    inputPer1m: 3.00,
    outputPer1m: 15.00,
  },
  "claude-opus-4": {
    name: "claude-opus-4",
    displayName: "Opus 4",
    inputPer1m: 15.00,
    outputPer1m: 75.00,
  },
};

class ModelRouter {
  constructor() {
    this.routingRules = [
      {
        taskType: "filing_lookup",
        model: "claude-3-5-haiku-20241022",
        reason: "Simple data retrieval — Haiku handles lookups at 1/4 the cost of Sonnet",
      },
      {
        taskType: "entity_resolution",
        model: "claude-sonnet-4",
        reason: "Moderate reasoning needed — Sonnet balances cost and capability for entity matching",
      },
      {
        taskType: "risk_analysis",
        model: "claude-opus-4",
        reason: "Complex multi-factor analysis — Opus provides deepest reasoning for risk assessment",
      },
      {
        taskType: "general",
        model: "claude-sonnet-4",
        reason: "General query — Sonnet is the default balanced choice",
      },
    ];

    this.taskKeywords = {
      filing_lookup: ["filing", "lookup", "search", "find", "list", "get", "fetch", "show"],
      entity_resolution: ["entity", "match", "resolve", "identify", "deduplicate", "merge", "link"],
      risk_analysis: ["risk", "analysis", "assess", "evaluate", "score", "exposure", "liability", "collateral"],
    };
  }

  /**
   * Classify a query into a task type based on keyword matching.
   * @param {string} query
   * @returns {string} Task type
   */
  classifyTask(query) {
    // TODO: Implement task classification
    // 1. Lowercase the query
    // 2. Check in priority order: risk_analysis, entity_resolution, filing_lookup
    // 3. For each task type, check if any keyword appears in the query
    // 4. Return first match, or "general" if no keywords match
  }

  /**
   * Determine which model to use for a given query.
   * @param {string} query
   * @param {string|null} taskType - Optional pre-classified task type
   * @returns {object} Routing decision with model, reason, costs
   */
  route(query, taskType = null) {
    // TODO: Implement routing
    // 1. If taskType is null, call classifyTask(query)
    // 2. Find matching routing rule
    // 3. Look up model pricing
    // 4. Return { model, displayName, taskType, reason, costPer1mInput, costPer1mOutput }
  }

  /**
   * Calculate dollar cost for a specific API call.
   * @param {string} model
   * @param {number} inputTokens
   * @param {number} outputTokens
   * @returns {object} { inputCost, outputCost, totalCost }
   */
  estimateCost(model, inputTokens, outputTokens) {
    // TODO: Implement cost estimation
    // inputCost = (inputTokens / 1_000_000) * pricing.inputPer1m
    // outputCost = (outputTokens / 1_000_000) * pricing.outputPer1m
  }

  /**
   * Compare routed cost vs all-Sonnet baseline.
   * @param {Array<{query: string, inputTokens: number, outputTokens: number}>} queries
   * @returns {object} { baselineCost, routedCost, savings, savingsPct }
   */
  compareRoutingVsBaseline(queries) {
    // TODO: Implement comparison
  }
}

// =============================================================================
// SELF-TEST
// =============================================================================

function selfTest() {
  console.log("=".repeat(60));
  console.log("M22 Lab — Model Router Self-Test");
  console.log("=".repeat(60));

  const router = new ModelRouter();

  const testQueries = [
    ["Find all UCC filings for Acme Corp", "filing_lookup", "claude-3-5-haiku-20241022"],
    ["Search for filings in Texas", "filing_lookup", "claude-3-5-haiku-20241022"],
    ["List all secured parties in New York", "filing_lookup", "claude-3-5-haiku-20241022"],
    ["Resolve entity: is 'Acme Corp' the same as 'ACME Corporation'?", "entity_resolution", "claude-sonnet-4"],
    ["Identify matching debtors across jurisdictions", "entity_resolution", "claude-sonnet-4"],
    ["Assess the risk exposure for Greenfield Logistics", "risk_analysis", "claude-opus-4"],
    ["Evaluate collateral coverage and liability risk", "risk_analysis", "claude-opus-4"],
    ["What is UCC Article 9?", "general", "claude-sonnet-4"],
  ];

  console.log("\n--- Routing Decisions ---");
  let allPassed = true;
  for (const [query, expectedType, expectedModel] of testQueries) {
    const result = router.route(query);
    const status = result.model === expectedModel ? "PASS" : "FAIL";
    if (status === "FAIL") allPassed = false;
    console.log(`\n  [${status}] "${query.slice(0, 50)}..."`);
    console.log(`    Task: ${result.taskType} | Model: ${result.displayName}`);
    console.log(`    Reason: ${result.reason}`);
    console.log(
      `    Cost: $${result.costPer1mInput.toFixed(2)}/$1M in, ` +
        `$${result.costPer1mOutput.toFixed(2)}/$1M out`
    );
  }

  console.log("\n--- Cost Estimation ---");
  const cost = router.estimateCost("claude-sonnet-4", 1500, 500);
  console.log(`  Sonnet: 1500 input + 500 output tokens`);
  console.log(
    `  Input: $${cost.inputCost.toFixed(6)}, Output: $${cost.outputCost.toFixed(6)}, ` +
      `Total: $${cost.totalCost.toFixed(6)}`
  );

  const costHaiku = router.estimateCost("claude-3-5-haiku-20241022", 1500, 500);
  console.log(`\n  Haiku:  1500 input + 500 output tokens`);
  console.log(
    `  Input: $${costHaiku.inputCost.toFixed(6)}, Output: $${costHaiku.outputCost.toFixed(6)}, ` +
      `Total: $${costHaiku.totalCost.toFixed(6)}`
  );

  const savings = ((1 - costHaiku.totalCost / cost.totalCost) * 100).toFixed(1);
  console.log(`\n  Haiku vs Sonnet savings: ${savings}%`);

  console.log("\n--- Routing vs Baseline Comparison ---");
  const sampleQueries = [
    { query: "Find filings for Acme", inputTokens: 800, outputTokens: 400 },
    { query: "Search filings in Texas", inputTokens: 900, outputTokens: 350 },
    { query: "Resolve entity Acme Corp vs ACME Corporation", inputTokens: 1200, outputTokens: 600 },
    { query: "Assess risk for Greenfield Logistics portfolio", inputTokens: 2000, outputTokens: 1000 },
    { query: "What is a UCC filing?", inputTokens: 500, outputTokens: 300 },
  ];
  const comparison = router.compareRoutingVsBaseline(sampleQueries);
  console.log(`  Baseline (all Sonnet): $${comparison.baselineCost.toFixed(6)}`);
  console.log(`  Routed:                $${comparison.routedCost.toFixed(6)}`);
  console.log(`  Savings:               $${comparison.savings.toFixed(6)} (${comparison.savingsPct.toFixed(1)}%)`);

  if (allPassed) {
    console.log("\n" + "=".repeat(60));
    console.log("All router tests passed!");
    console.log("=".repeat(60));
  }
}

selfTest();

module.exports = { ModelRouter, MODEL_PRICING };
