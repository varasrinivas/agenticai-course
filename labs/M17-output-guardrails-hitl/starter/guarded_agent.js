/**
 * M17: Guarded Agent — Starter
 * Composes all four guardrails into a single protected agent runner.
 */
import { validateOutput } from "./output_validator.js";
import { CostController } from "./cost_controller.js";
import { CircuitBreaker, CircuitState } from "./circuit_breaker.js";
import { HITLGate } from "./hitl_gate.js";

// ── Mock Agent Responses ────────────────────────────────────
const MOCK_RESPONSES = {
  clean_query: {
    entity: "Acme Corporation",
    filing_number: "UCC-2024-CA-0001234",
    response: "Acme Corporation has 3 active UCC filings in California. The most recent was filed on 2024-01-15.",
    confidence: 0.95,
    input_tokens: 500,
    output_tokens: 200,
  },
  low_confidence: {
    entity: "XYZ Holdings",
    filing_number: "UCC-2024-NY-0005678",
    response: "I think XYZ Holdings might have some filings, but I'm not sure about the exact count.",
    confidence: 0.55,
    input_tokens: 600,
    output_tokens: 250,
  },
  medium_confidence: {
    entity: "Smith Industries",
    filing_number: "UCC-2024-TX-0009012",
    response: "Smith Industries has filings in Texas matching the search criteria.",
    confidence: 0.82,
    input_tokens: 550,
    output_tokens: 220,
  },
  pii_leak: {
    entity: "John Doe",
    filing_number: "UCC-2024-FL-0003456",
    response: "John Doe (SSN: 123-45-6789) has 2 filings. Contact: john@example.com or 555-867-5309.",
    confidence: 0.90,
    input_tokens: 700,
    output_tokens: 300,
  },
  expensive_query: {
    entity: "MegaCorp International",
    filing_number: "UCC-2024-WA-0007890",
    response: "MegaCorp International has extensive filing history across 12 states.",
    confidence: 0.92,
    input_tokens: 80000,
    output_tokens: 30000,
  },
};

const EXPECTED_FIELDS = ["entity", "filing_number", "response", "confidence"];

function mockAgentCall(queryType) {
  return MOCK_RESPONSES[queryType] || MOCK_RESPONSES.clean_query;
}

export class GuardedAgent {
  /**
   * @param {number} budgetLimit - Max cost per request session.
   * @param {number} failureThreshold - Failures before circuit breaker trips.
   */
  constructor(budgetLimit = 0.50, failureThreshold = 3) {
    // TODO 1: Initialize all four guardrail components:
    //   this.costController = new CostController(budgetLimit);
    //   this.circuitBreaker = new CircuitBreaker(failureThreshold, 60.0);
    //   this.hitlGate = new HITLGate(true);
    //   this.results = [];
  }

  /**
   * Run an agent call with all guardrails active.
   * @param {string} queryType - Key into MOCK_RESPONSES.
   * @returns {Promise<Object>}
   */
  async runGuarded(queryType) {
    const result = {
      status: "allowed",
      queryType,
      reason: "",
      agentOutput: null,
      guardrailDetails: {
        circuitBreaker: {},
        cost: {},
        validation: {},
        hitl: null,
      },
    };

    // TODO 2: Check circuit breaker — if canExecute() is false, block.

    // TODO 3: Get mock agent response and pre-check budget with wouldExceed().

    // TODO 4: Track the token usage.

    // TODO 5: Validate the output.

    // TODO 6: Route through HITL gate using confidence.

    // TODO 7: Record success/failure with circuit breaker.

    // TODO 8: Push result to this.results and return.

    return result;
  }

  getSummary() {
    return {
      totalRuns: (this.results || []).length,
      results: this.results || [],
      costSummary: (this.costController || new CostController()).getSummary(),
      circuitBreakerState: (this.circuitBreaker || new CircuitBreaker()).getState(),
      hitlStats: (this.hitlGate || new HITLGate()).getStats(),
    };
  }
}

// ── Self-Test ───────────────────────────────────────────────
const isMain = process.argv[1] && (
  process.argv[1].endsWith("guarded_agent.js") ||
  process.argv[1].endsWith("guarded_agent.mjs")
);

if (isMain) {
  console.log("=".repeat(60));
  console.log("M17 Guarded Agent — Self-Test");
  console.log("=".repeat(60));

  const agent = new GuardedAgent(0.50, 3);

  const scenarios = [
    ["Scenario 1: Clean Query", "clean_query"],
    ["Scenario 2: Expensive Query (budget check)", "expensive_query"],
    ["Scenario 3: PII Leak (output validation)", "pii_leak"],
    ["Scenario 4: Low Confidence (auto-deny)", "low_confidence"],
    ["Scenario 5: Medium Confidence (HITL review)", "medium_confidence"],
  ];

  for (const [label, queryType] of scenarios) {
    console.log("\n" + "-".repeat(50));
    console.log(label);
    console.log("-".repeat(50));
    const result = await agent.runGuarded(queryType);
    console.log(`  Status: ${result.status}`);
    console.log(`  Reason: ${result.reason}`);
  }

  const summary = agent.getSummary();
  console.log(`\n${"=".repeat(60)}`);
  console.log("Guarded Agent Summary");
  console.log("=".repeat(60));
  console.log(`  Total runs: ${summary.totalRuns}`);
  console.log(`  Cost: $${summary.costSummary.totalCost.toFixed(6)}`);
  console.log(`  Circuit breaker: ${summary.circuitBreakerState.state}`);
  console.log(`  HITL decisions: ${summary.hitlStats.totalDecisions}`);

  console.log("\n" + "=".repeat(60));
  console.log("Self-test complete. Fill in TODOs to see all guardrails working together.");
  console.log("=".repeat(60));
}
