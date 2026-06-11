/**
 * M17 Lab: Output Guardrails & HITL (Node.js)
 * ============================================
 * Hallucination detector + cost budget + circuit breaker + approval gate.
 * Run: node output_pipeline.js
 */

import OpenAI from "openai";
import * as readline from "node:readline/promises";

const client = new OpenAI({ baseURL: "http://localhost:11434/v1", apiKey: "ollama" });

// ── Part 1: Hallucination Detector (Mistral-as-Judge) ────────
const HALLUCINATION_PROMPT = (sources, response) => `You are a fact-checking judge. Compare the response
against the source documents. For each factual claim, classify it as:
- "supported": Directly backed by sources
- "unsupported": NOT in sources (possible hallucination)
- "contradicted": CONTRADICTS sources (definite error)

Respond with ONLY JSON:
{"claims": [{"text": "claim", "status": "supported|unsupported|contradicted"}],
 "overall": "pass|flag|block", "unsupported_count": 0}

Sources:

${sources}


Response to check:

${response}
`;

/**
 * TODO:
 * 1. const sources = sourceDocs.join("\n---\n");
 * 2. Call the model with HALLUCINATION_PROMPT(sources, responseText)
 * 3. Parse JSON (strip ``` fences); treat unknown claim statuses as "unsupported"
 * 4. Decision logic:
 *    - any "contradicted" → { result: "block", reason: "N contradicted claim(s)", claims }
 *    - >= 2 "unsupported" → { result: "flag", reason, claims }
 *    - else → { result: "pass", claims }
 * 5. On ANY error → { result: "flag", reason: `Check failed: ${e}`, claims: [] }
 *    ← quality gates degrade to HUMAN REVIEW (flag), not silently to pass
 */
async function checkHallucination(responseText, sourceDocs) {
  // TODO: implement
}

// ── Part 2: Cost Tracker ─────────────────────────────────────
const INPUT_PRICE = 2.0 / 1_000_000;   // ~$2/M input tokens (cloud)
const OUTPUT_PRICE = 6.0 / 1_000_000;  // ~$6/M output tokens (cloud)

class CostTracker {
  constructor(budgetDollars = 0.5) {
    this.budgetDollars = budgetDollars;
    this.inputTokens = 0;
    this.outputTokens = 0;
  }

  get totalCost() {
    return this.inputTokens * INPUT_PRICE + this.outputTokens * OUTPUT_PRICE;
  }

  recordUsage(inputToks, outputToks) {
    this.inputTokens += inputToks;
    this.outputTokens += outputToks;
  }

  /**
   * TODO: const estimatedCost = estimatedInput * INPUT_PRICE +
   *                             estimatedOutput * OUTPUT_PRICE;
   *       return this.totalCost + estimatedCost <= this.budgetDollars;
   */
  canAfford(estimatedInput = 5000, estimatedOutput = 1000) {
    // TODO: implement
  }

  summary() {
    return `Tokens: ${this.inputTokens} in / ${this.outputTokens} out | Cost: $${this.totalCost.toFixed(4)} / $${this.budgetDollars.toFixed(2)}`;
  }
}

// ── Part 3: Circuit Breaker ──────────────────────────────────
class CircuitBreaker {
  constructor(failureThreshold = 3, cooldownSeconds = 5.0) {
    this.failureThreshold = failureThreshold;
    this.cooldownSeconds = cooldownSeconds;
    this.state = "closed"; // closed | open | half_open
    this.failureCount = 0;
    this.openedAt = 0;
  }

  /**
   * TODO:
   * - "closed" → true
   * - "open" → if (Date.now() - this.openedAt) / 1000 >= this.cooldownSeconds:
   *     this.state = "half_open"; return true (ONE test request)
   *   else return false
   * - "half_open" → false (a test is already in flight)
   */
  canExecute() {
    // TODO: implement
  }

  /** TODO: "half_open" → "closed". Always reset failureCount to 0. */
  recordSuccess() {
    // TODO: implement
  }

  /**
   * TODO:
   * - failureCount++
   * - "half_open" → "open", openedAt = now, cooldownSeconds *= 2 (backoff)
   * - else if failureCount >= failureThreshold → "open", openedAt = now
   */
  recordFailure() {
    // TODO: implement
  }
}

// ── Part 4: Approval Gate (COMPLETE) ─────────────────────────
async function approvalGate(action, context, autoApprove = false) {
  console.log(`\n${"=".repeat(50)}`);
  console.log("APPROVAL REQUIRED");
  console.log(`Action: ${action}`);
  console.log(`Context: ${context}`);
  console.log("=".repeat(50));

  if (autoApprove) {
    console.log("  [Auto-approved for testing]");
    return { approved: true, modified: false };
  }

  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  const response = (await rl.question("Approve? (y/n/e to edit): ")).trim().toLowerCase();
  if (response === "e") {
    const newAction = (await rl.question("Enter modified action: ")).trim();
    rl.close();
    return { approved: true, modified: true, new_action: newAction };
  }
  rl.close();
  if (response === "y") return { approved: true, modified: false };
  return { approved: false, reason: "Human denied" };
}

// ── Test Suite (COMPLETE) ────────────────────────────────────
const sourceDocs = [
  "UCC Filing #2024-NY-0042: Filed March 22, 2024 by Acme Corp. " +
    "Collateral: $2.3M in manufacturing equipment. Status: Active.",
  "Amendment filed April 10, 2024: Added collateral description " +
    "for warehouse inventory valued at $890K.",
];

console.log("-".repeat(60));
console.log("TEST 1: Hallucination Detection — Contradicted Claim");
const result = await checkHallucination(
  "The UCC filing was submitted on March 15, 2024 by Acme Corp for $2.3M " +
    "in equipment collateral. An amendment was filed on April 10, 2024 " +
    "adding $890K in warehouse inventory.",
  sourceDocs
);
console.log(`  Result: ${result.result} — ${result.reason ?? "All claims supported"}`);
for (const c of result.claims ?? []) console.log(`    [${c.status}] ${String(c.text).slice(0, 70)}`);

console.log("\n" + "-".repeat(60));
console.log("TEST 2: Hallucination Detection — All Supported");
const result2 = await checkHallucination(
  "The UCC filing was submitted on March 22, 2024 by Acme Corp for $2.3M in equipment collateral.",
  sourceDocs
);
console.log(`  Result: ${result2.result}`);

console.log("\n" + "-".repeat(60));
console.log("TEST 3: Cost Tracking & Budget Enforcement");
const tracker = new CostTracker(0.1);
for (let i = 0; i < 5; i++) {
  if (!tracker.canAfford(8000, 2000)) {
    console.log(`  Iteration ${i + 1}: BUDGET EXCEEDED — ${tracker.summary()}`);
    break;
  }
  tracker.recordUsage(8000, 2000);
  console.log(`  Iteration ${i + 1}: ${tracker.summary()}`);
}

console.log("\n" + "-".repeat(60));
console.log("TEST 4: Circuit Breaker State Transitions");
const breaker = new CircuitBreaker(3, 2);
const actions = [
  ["success", "Normal request 1"],
  ["failure", "API error 1"],
  ["failure", "API error 2"],
  ["failure", "API error 3 -> TRIPS"],
  ["blocked", "Request during OPEN state"],
];
for (const [action, label] of actions) {
  if (!breaker.canExecute()) {
    console.log(`  ${label}: BLOCKED (state=${breaker.state})`);
    continue;
  }
  if (action === "success") {
    breaker.recordSuccess();
    console.log(`  ${label}: OK (state=${breaker.state})`);
  } else {
    breaker.recordFailure();
    console.log(`  ${label}: FAIL (state=${breaker.state}, failures=${breaker.failureCount}/${breaker.failureThreshold})`);
  }
}
console.log(`  Waiting ${breaker.cooldownSeconds}s for cooldown...`);
await new Promise((r) => setTimeout(r, breaker.cooldownSeconds * 1000 + 100));
console.log(`  Half-open test: canExecute=${breaker.canExecute()} (state=${breaker.state})`);
breaker.recordSuccess();
console.log(`  Test passed -> state=${breaker.state}`);

console.log("\n" + "-".repeat(60));
console.log("TEST 5: Approval Gate (auto-approved for testing)");
const gateResult = await approvalGate(
  "Send $450 refund to Order #12345",
  "Customer received damaged item, within return window",
  true
);
console.log(`  Result:`, gateResult);
