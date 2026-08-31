/**
 * M22 Lab — Model Router (Solution)
 * ===================================
 * Complete model router with task classification and cost estimation.
 *
 * Usage:
 *     node model_router.js
 */

const MODEL_PRICING = {
  "claude-haiku-4-5-20251001": {
    name: "claude-haiku-4-5-20251001",
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
        model: "claude-haiku-4-5-20251001",
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

  classifyTask(query) {
    const queryLower = query.toLowerCase();
    for (const taskType of ["risk_analysis", "entity_resolution", "filing_lookup"]) {
      if (this.taskKeywords[taskType].some((kw) => queryLower.includes(kw))) {
        return taskType;
      }
    }
    return "general";
  }

  route(query, taskType = null) {
    if (!taskType) taskType = this.classifyTask(query);

    const rule = this.routingRules.find((r) => r.taskType === taskType) ||
      this.routingRules.find((r) => r.taskType === "general");

    const pricing = MODEL_PRICING[rule.model];
    return {
      model: rule.model,
      displayName: pricing.displayName,
      taskType,
      reason: rule.reason,
      costPer1mInput: pricing.inputPer1m,
      costPer1mOutput: pricing.outputPer1m,
    };
  }

  estimateCost(model, inputTokens, outputTokens) {
    const pricing = MODEL_PRICING[model];
    const inputCost = (inputTokens / 1_000_000) * pricing.inputPer1m;
    const outputCost = (outputTokens / 1_000_000) * pricing.outputPer1m;
    return { inputCost, outputCost, totalCost: inputCost + outputCost };
  }

  compareRoutingVsBaseline(queries) {
    let baselineTotal = 0;
    let routedTotal = 0;

    for (const q of queries) {
      const baseline = this.estimateCost("claude-sonnet-4", q.inputTokens, q.outputTokens);
      baselineTotal += baseline.totalCost;

      const routing = this.route(q.query);
      const routed = this.estimateCost(routing.model, q.inputTokens, q.outputTokens);
      routedTotal += routed.totalCost;
    }

    const savings = baselineTotal - routedTotal;
    const savingsPct = baselineTotal > 0 ? (savings / baselineTotal) * 100 : 0;

    return { baselineCost: baselineTotal, routedCost: routedTotal, savings, savingsPct };
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
    ["Find all UCC filings for Acme Corp", "filing_lookup", "claude-haiku-4-5-20251001"],
    ["Search for filings in Texas", "filing_lookup", "claude-haiku-4-5-20251001"],
    ["List all secured parties in New York", "filing_lookup", "claude-haiku-4-5-20251001"],
    ["Resolve entity: is 'Acme Corp' the same as 'ACME Corporation'?", "entity_resolution", "claude-sonnet-4"],
    ["Identify matching debtors across jurisdictions", "entity_resolution", "claude-sonnet-4"],
    ["Assess the risk exposure for Greenfield Logistics", "risk_analysis", "claude-opus-4"],
    ["Evaluate collateral coverage and liability risk", "risk_analysis", "claude-opus-4"],
    ["What is UCC Article 9?", "general", "claude-sonnet-4"],
  ];

  console.log("\n--- Routing Decisions ---");
  let allPassed = true;
  for (const [query, , expectedModel] of testQueries) {
    const result = router.route(query);
    const status = result.model === expectedModel ? "PASS" : "FAIL";
    if (status === "FAIL") allPassed = false;
    console.log(`\n  [${status}] "${query.slice(0, 50)}..."`);
    console.log(`    Task: ${result.taskType} | Model: ${result.displayName}`);
    console.log(`    Reason: ${result.reason}`);
  }

  console.log("\n--- Cost Estimation ---");
  const cost = router.estimateCost("claude-sonnet-4", 1500, 500);
  console.log(`  Sonnet: $${cost.totalCost.toFixed(6)}`);

  const costHaiku = router.estimateCost("claude-haiku-4-5-20251001", 1500, 500);
  console.log(`  Haiku:  $${costHaiku.totalCost.toFixed(6)}`);
  console.log(`  Savings: ${((1 - costHaiku.totalCost / cost.totalCost) * 100).toFixed(1)}%`);

  console.log("\n--- Routing vs Baseline ---");
  const comparison = router.compareRoutingVsBaseline([
    { query: "Find filings for Acme", inputTokens: 800, outputTokens: 400 },
    { query: "Search filings in Texas", inputTokens: 900, outputTokens: 350 },
    { query: "Resolve entity Acme Corp vs ACME Corporation", inputTokens: 1200, outputTokens: 600 },
    { query: "Assess risk for Greenfield Logistics portfolio", inputTokens: 2000, outputTokens: 1000 },
    { query: "What is a UCC filing?", inputTokens: 500, outputTokens: 300 },
  ]);
  console.log(`  Baseline: $${comparison.baselineCost.toFixed(6)}`);
  console.log(`  Routed:   $${comparison.routedCost.toFixed(6)}`);
  console.log(`  Savings:  $${comparison.savings.toFixed(6)} (${comparison.savingsPct.toFixed(1)}%)`);

  if (allPassed) {
    console.log("\n" + "=".repeat(60));
    console.log("All router tests passed!");
    console.log("=".repeat(60));
  }
}

selfTest();

export { ModelRouter, MODEL_PRICING };
