/**
 * M22 Lab — Optimized Agent (Solution)
 * ======================================
 * Complete optimization pipeline with side-by-side cost comparison.
 *
 * Usage:
 *     node optimized_agent.js
 */

const { ResponseCache } = require("./response_cache");
const { ModelRouter, MODEL_PRICING } = require("./model_router");
const { TokenOptimizer } = require("./token_optimizer");
const { CostTracker } = require("./cost_tracker");

const SYSTEM_PROMPT = `You are an AI assistant that specializes in UCC filing research and analysis.
You should always provide accurate, detailed information about Uniform Commercial Code filings.
Please ensure that you check all relevant databases prior to responding to any query.
It is important that you identify the secured party, debtor, and collateral description
in each filing. Make sure to always include the filing number, jurisdiction, and filing date.
Please provide responses in a clear, structured format with bullet points.
In order to help the user effectively, you must always cross-reference entity names
due to the fact that companies sometimes file under different names or abbreviations.
For the purpose of risk assessment, take into consideration the filing date, the collateral
type, the number of amendments, and whether the filing has been continued or terminated
subsequent to the original filing date. In the event that a filing has the ability to be
matched to multiple entities, please make sure to list all possible matches with regard
to the debtor name. You are an AI assistant that is able to handle complex UCC queries
on a regular basis in a timely manner.`;

const MOCK_RESPONSES = {
  filing_lookup: { answer: "Found 3 UCC filings matching your query.", inputTokens: 850, outputTokens: 380 },
  entity_resolution: { answer: "Entity resolution complete. Confirmed same legal entity.", inputTokens: 1200, outputTokens: 520 },
  risk_analysis: { answer: "Risk assessment: MODERATE risk. Total secured debt: $2.4M.", inputTokens: 2200, outputTokens: 890 },
  general: { answer: "UCC Article 9 governs secured transactions.", inputTokens: 650, outputTokens: 280 },
};

function mockApiCall(model, systemPrompt, query, taskType) {
  const data = MOCK_RESPONSES[taskType] || MOCK_RESPONSES.general;
  const jitter = 0.85 + Math.random() * 0.3;
  return {
    answer: data.answer,
    inputTokens: Math.floor(data.inputTokens * jitter),
    outputTokens: Math.floor(data.outputTokens * jitter),
    model,
  };
}

class OptimizedAgent {
  constructor(cacheTtl = 300, cacheMax = 1000) {
    this.cache = new ResponseCache(cacheTtl, cacheMax);
    this.router = new ModelRouter();
    this.optimizer = new TokenOptimizer(8);
    this.tracker = new CostTracker();
    this.systemPrompt = SYSTEM_PROMPT;

    this.promptSavings = this.optimizer.compressSystemPrompt(SYSTEM_PROMPT);
    this.optimizedPrompt = this.promptSavings.compressed;
  }

  run(query) {
    // Check cache
    const cached = this.cache.get(query);
    if (cached) {
      this.tracker.record(
        cached.model || "claude-sonnet-4",
        cached.inputTokens || 500,
        cached.outputTokens || 200,
        true
      );
      return {
        answer: cached.answer,
        model: cached.model || "unknown",
        taskType: cached.taskType || "unknown",
        cached: true,
        cost: 0.0,
        cacheStats: this.cache.getStats(),
      };
    }

    // Route
    const routing = this.router.route(query);

    // Execute
    const response = mockApiCall(routing.model, this.optimizedPrompt, query, routing.taskType);

    // Track
    const record = this.tracker.record(routing.model, response.inputTokens, response.outputTokens);

    // Cache
    this.cache.set(query, {
      answer: response.answer,
      model: routing.model,
      taskType: routing.taskType,
      inputTokens: response.inputTokens,
      outputTokens: response.outputTokens,
    });

    return {
      answer: response.answer,
      model: routing.model,
      modelDisplay: routing.displayName,
      taskType: routing.taskType,
      routingReason: routing.reason,
      cached: false,
      cost: record.cost,
      inputTokens: response.inputTokens,
      outputTokens: response.outputTokens,
      cacheStats: this.cache.getStats(),
    };
  }

  runBatch(queries) {
    const results = [];
    for (const query of queries) {
      const cached = this.cache.get(query);
      if (cached) {
        this.tracker.record(cached.model || "claude-sonnet-4", cached.inputTokens || 500, cached.outputTokens || 200, true);
        results.push({ answer: cached.answer, model: cached.model, cached: true, batch: true, cost: 0.0 });
        continue;
      }

      const routing = this.router.route(query);
      const response = mockApiCall(routing.model, this.optimizedPrompt, query, routing.taskType);
      const record = this.tracker.record(routing.model, response.inputTokens, response.outputTokens, false, true);

      this.cache.set(query, {
        answer: response.answer,
        model: routing.model,
        taskType: routing.taskType,
        inputTokens: response.inputTokens,
        outputTokens: response.outputTokens,
      });

      results.push({
        answer: response.answer,
        model: routing.model,
        modelDisplay: routing.displayName,
        taskType: routing.taskType,
        cached: false,
        batch: true,
        cost: record.cost,
      });
    }
    return results;
  }

  compareCosts(queries) {
    // Optimized (fresh components — run first to collect actual token counts)
    this.cache = new ResponseCache(300, 1000);
    this.tracker = new CostTracker();

    for (const query of queries) {
      this.run(query);
    }

    // Baseline: All Sonnet, no cache, same token counts as optimized run
    const baselineTracker = new CostTracker();
    for (const record of this.tracker.records) {
      baselineTracker.record("claude-sonnet-4", record.inputTokens, record.outputTokens);
    }
    const baselineTotal = baselineTracker.getTotalCost();
    const baselineAvg = queries.length > 0 ? baselineTotal / queries.length : 0;

    const optimizedTotal = this.tracker.getTotalCost();
    const optimizedAvg = queries.length > 0 ? optimizedTotal / queries.length : 0;

    const cacheInfo = this.tracker.getSavingsFromCache();
    const byModel = this.tracker.getCostByModel();

    const savingsAmount = baselineTotal - optimizedTotal;
    const savingsPct = baselineTotal > 0 ? (savingsAmount / baselineTotal) * 100 : 0;

    const countNonCached = (model) => {
      const data = byModel[model];
      if (!data) return 0;
      return data.calls - this.tracker.records.filter((r) => r.model === model && r.cached).length;
    };

    const haikuCalls = countNonCached("claude-haiku-3-5");
    const sonnetCalls = countNonCached("claude-sonnet-4");
    const opusCalls = countNonCached("claude-opus-4");
    const cacheHitPct = queries.length > 0 ? (cacheInfo.cacheHits / queries.length) * 100 : 0;

    const lines = [
      "",
      "=".repeat(50),
      "       COST OPTIMIZATION REPORT",
      "=".repeat(50),
      "",
      "Baseline (all Sonnet, no cache):",
      `  Queries:        ${queries.length}`,
      `  Total cost:     $${baselineTotal.toFixed(4)}`,
      `  Avg cost/query: $${baselineAvg.toFixed(4)}`,
      "",
      "Optimized (routing + cache):",
      `  Queries:        ${queries.length}`,
      `  Cache hits:     ${cacheInfo.cacheHits} (${cacheHitPct.toFixed(0)}%)`,
      `  Model routing:  ${haikuCalls} Haiku, ${sonnetCalls} Sonnet, ${opusCalls} Opus`,
      `  Total cost:     $${optimizedTotal.toFixed(4)}`,
      `  Avg cost/query: $${optimizedAvg.toFixed(4)}`,
      "",
      `Savings: $${savingsAmount.toFixed(4)} (${savingsPct.toFixed(1)}% reduction)`,
      "",
      "--- Prompt Compression ---",
      `  Original:   ${this.promptSavings.originalTokens} tokens`,
      `  Compressed: ${this.promptSavings.compressedTokens} tokens`,
      `  Reduction:  ${this.promptSavings.reductionPct.toFixed(1)}%`,
      "",
      "=".repeat(50),
    ];

    return lines.join("\n");
  }
}

// =============================================================================
// SELF-TEST
// =============================================================================

function selfTest() {
  console.log("=".repeat(60));
  console.log("M22 Lab — Optimized Agent Self-Test");
  console.log("=".repeat(60));

  const testQueries = [
    "Find all UCC filings for Acme Corp in New York",
    "Search for filings in Texas filed in 2024",
    "List all secured parties in California",
    "Resolve entity: is 'Acme Corp' the same as 'ACME Corporation'?",
    "Find all UCC filings for Acme Corp in New York",
    "Assess the risk exposure for Greenfield Logistics",
    "Find filings for Nextera Holdings in Delaware",
    "What is a UCC continuation statement?",
    "Search for filings in Texas filed in 2024",
    "Identify matching debtors across NY and TX jurisdictions",
    "Evaluate collateral coverage for the Acme portfolio",
    "Find all UCC filings for Acme Corp in New York",
    "List amendment history for filing #NY-2024-001",
    "What are the requirements for a UCC-3 filing?",
    "Assess the risk exposure for Greenfield Logistics",
    "Find filings where equipment is listed as collateral",
    "Resolve entity: Nextera Holdings vs NextEra Holdings Inc",
    "Search for filings in Texas filed in 2024",
    "Generate risk report for all NY filings expiring in 90 days",
    "Find all UCC filings for Acme Corp in New York",
  ];

  // Show query-by-query
  console.log("\n--- Query-by-Query Results ---");
  const agentFresh = new OptimizedAgent(300, 100);
  for (let i = 0; i < testQueries.length; i++) {
    const result = agentFresh.run(testQueries[i]);
    const cachedTag = result.cached ? " [CACHED]" : "";
    const modelTag = result.modelDisplay || result.model || "cached";
    const q = testQueries[i].slice(0, 55).padEnd(55);
    console.log(`  Q${String(i + 1).padStart(2)}: ${q} -> ${modelTag.padEnd(10)} $${result.cost.toFixed(4)}${cachedTag}`);
  }

  // Comparison
  const agent = new OptimizedAgent(300, 100);
  const report = agent.compareCosts(testQueries);
  console.log(report);

  console.log("\n" + "=".repeat(60));
  console.log("Optimization pipeline complete!");
  console.log("=".repeat(60));
}

selfTest();

module.exports = { OptimizedAgent };
