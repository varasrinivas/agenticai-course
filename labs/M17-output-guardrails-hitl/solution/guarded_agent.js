/**
 * M17: Guarded Agent — Solution
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
  constructor(budgetLimit = 0.50, failureThreshold = 3) {
    this.costController = new CostController(budgetLimit);
    this.circuitBreaker = new CircuitBreaker(failureThreshold, 60.0);
    this.hitlGate = new HITLGate(true);
    this.results = [];
  }

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

    // Step 1: Check circuit breaker
    const cbState = this.circuitBreaker.getState();
    result.guardrailDetails.circuitBreaker = cbState;

    if (!this.circuitBreaker.canExecute()) {
      result.status = "blocked";
      result.reason = `Circuit breaker is ${cbState.state} — ${cbState.failureCount} consecutive failures`;
      this.results.push(result);
      return result;
    }

    // Step 2: Get mock response and pre-check budget
    const agentResponse = mockAgentCall(queryType);
    const budgetCheck = this.costController.wouldExceed(
      agentResponse.input_tokens,
      agentResponse.output_tokens
    );
    result.guardrailDetails.cost = budgetCheck;

    if (budgetCheck.wouldExceed) {
      result.status = "blocked";
      result.reason = `Budget exceeded — call would cost $${budgetCheck.estimatedCost.toFixed(6)}, only $${(budgetCheck.budgetAfter + budgetCheck.estimatedCost).toFixed(6)} remaining`;
      this.results.push(result);
      return result;
    }

    // Step 3: Track the cost
    const costResult = this.costController.trackUsage(
      agentResponse.input_tokens,
      agentResponse.output_tokens
    );
    result.guardrailDetails.cost = costResult;

    // Step 4: Validate output
    const outputForValidation = {};
    for (const [k, v] of Object.entries(agentResponse)) {
      if (k !== "input_tokens" && k !== "output_tokens") {
        outputForValidation[k] = v;
      }
    }
    const validation = validateOutput(outputForValidation, EXPECTED_FIELDS);
    result.guardrailDetails.validation = validation;

    if (!validation.valid) {
      this.circuitBreaker.recordFailure();
      result.status = "blocked";
      const reasons = [];
      if (!validation.checks.structure.valid) {
        reasons.push(`missing fields: ${JSON.stringify(validation.checks.structure.missingFields)}`);
      }
      if (validation.checks.pii.hasPii) {
        reasons.push(`PII detected: ${JSON.stringify(validation.checks.pii.piiTypes)}`);
      }
      result.reason = `Output validation failed — ${reasons.join("; ")}`;
      result.agentOutput = validation.output;
      this.results.push(result);
      return result;
    }

    // Step 5: Route by confidence through HITL gate
    const confidence = agentResponse.confidence || 0.5;
    const hallucinationPenalty = validation.checks.hallucination.confidencePenalty;
    const adjustedConfidence = Math.max(0.0, confidence - hallucinationPenalty);

    const hitlResult = await this.hitlGate.process(adjustedConfidence, outputForValidation);
    result.guardrailDetails.hitl = hitlResult;

    if (hitlResult.finalAction === "deny") {
      result.status = "denied";
      result.reason = `Low confidence (${(adjustedConfidence * 100).toFixed(0)}%) — auto-denied by HITL gate`;
    } else if (hitlResult.humanReviewed) {
      result.status = "reviewed";
      result.reason = `Medium confidence (${(adjustedConfidence * 100).toFixed(0)}%) — approved after HITL review`;
    } else {
      result.status = "allowed";
      result.reason = `High confidence (${(adjustedConfidence * 100).toFixed(0)}%) — auto-approved`;
    }

    result.agentOutput = validation.output;

    // Step 6: Record success/failure
    if (result.status !== "denied") {
      this.circuitBreaker.recordSuccess();
    } else {
      this.circuitBreaker.recordFailure();
    }

    this.results.push(result);
    return result;
  }

  getSummary() {
    return {
      totalRuns: this.results.length,
      results: this.results,
      costSummary: this.costController.getSummary(),
      circuitBreakerState: this.circuitBreaker.getState(),
      hitlStats: this.hitlGate.getStats(),
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
  console.log("All tests complete.");
  console.log("=".repeat(60));
}
