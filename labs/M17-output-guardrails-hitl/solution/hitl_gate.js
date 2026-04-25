/**
 * M17: HITL Approval Gate — Solution
 * Routes decisions by confidence level: auto-approve, human review, or auto-deny.
 * Domain context: UCC entity matching where partial matches need human verification.
 */
import * as readline from "readline";

// ── Confidence Thresholds ───────────────────────────────────
const AUTO_APPROVE_THRESHOLD = 0.9;
const HITL_REVIEW_THRESHOLD = 0.7;

/**
 * Route a decision based on confidence score.
 */
export function routeDecision(confidence, context) {
  const entity = context.entity || "unknown";

  if (confidence > AUTO_APPROVE_THRESHOLD) {
    return {
      action: "approve",
      reason: `High confidence (${(confidence * 100).toFixed(0)}%) match for '${entity}' — auto-approved`,
      confidence,
      requiresHuman: false,
    };
  } else if (confidence >= HITL_REVIEW_THRESHOLD) {
    return {
      action: "review",
      reason: `Medium confidence (${(confidence * 100).toFixed(0)}%) match for '${entity}' — requires human review`,
      confidence,
      requiresHuman: true,
    };
  } else {
    return {
      action: "deny",
      reason: `Low confidence (${(confidence * 100).toFixed(0)}%) match for '${entity}' — auto-denied`,
      confidence,
      requiresHuman: false,
    };
  }
}

/**
 * Simulate human review of a decision.
 */
export async function simulateHumanReview(context, autoMode = true) {
  if (autoMode) {
    return {
      approved: true,
      reviewer: "auto-test",
      notes: "Auto-approved in test mode",
    };
  }

  // Interactive mode
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });

  const ask = (q) => new Promise((resolve) => rl.question(q, resolve));

  console.log("\n" + "=".repeat(40));
  console.log("HUMAN REVIEW REQUIRED");
  console.log("=".repeat(40));
  for (const [key, value] of Object.entries(context)) {
    console.log(`  ${key}: ${value}`);
  }
  console.log("=".repeat(40));

  const response = await ask("Approve this match? (y/n): ");
  const notes = await ask("Reviewer notes (optional): ");
  rl.close();

  return {
    approved: ["y", "yes"].includes(response.trim().toLowerCase()),
    reviewer: "human",
    notes: notes.trim() || "No notes provided",
  };
}

export class HITLGate {
  constructor(autoMode = true) {
    this.autoMode = autoMode;
    this.decisions = [];
    this.reviewQueue = [];
    this.stats = { approved: 0, denied: 0, reviewed: 0 };
  }

  async process(confidence, context) {
    const routing = routeDecision(confidence, context);
    let reviewResult = null;
    let humanReviewed = false;
    let finalAction;

    if (routing.action === "approve") {
      finalAction = "approve";
      this.stats.approved += 1;
    } else if (routing.action === "deny") {
      finalAction = "deny";
      this.stats.denied += 1;
    } else {
      // Review needed
      reviewResult = await simulateHumanReview(context, this.autoMode);
      humanReviewed = true;
      this.stats.reviewed += 1;
      if (reviewResult.approved) {
        finalAction = "approve";
        this.stats.approved += 1;
      } else {
        finalAction = "deny";
        this.stats.denied += 1;
      }
    }

    const decision = {
      finalAction,
      routedAction: routing.action,
      confidence,
      humanReviewed,
      reviewResult,
    };
    this.decisions.push(decision);

    return decision;
  }

  getStats() {
    return {
      totalDecisions: this.decisions.length,
      approved: this.stats.approved,
      denied: this.stats.denied,
      humanReviewed: this.stats.reviewed,
      decisions: this.decisions,
    };
  }

  getPendingReviews() {
    return this.reviewQueue;
  }
}

// ── Self-Test ───────────────────────────────────────────────
const isMain = process.argv[1] && (
  process.argv[1].endsWith("hitl_gate.js") ||
  process.argv[1].endsWith("hitl_gate.mjs")
);

if (isMain) {
  console.log("=".repeat(60));
  console.log("M17 HITL Approval Gate — Self-Test");
  console.log("=".repeat(60));

  const gate = new HITLGate(true);

  const testCases = [
    [0.95, { entity: "Acme Corp", match: "Acme Corporation", filing: "UCC-2024-CA-0001234" }],
    [0.85, { entity: "Smith Holdings", match: "Smith Holding Co", filing: "UCC-2024-NY-0005678" }],
    [0.75, { entity: "Doe Industries", match: "Doe Industrial LLC", filing: "UCC-2024-TX-0009012" }],
    [0.60, { entity: "XYZ Corp", match: "XYZ Company Inc", filing: "UCC-2024-FL-0003456" }],
    [0.45, { entity: "Unknown LLC", match: "Unknown Limited", filing: "UCC-2024-WA-0007890" }],
  ];

  for (const [confidence, context] of testCases) {
    const result = await gate.process(confidence, context);
    const pct = (confidence * 100).toFixed(0);
    console.log(`\nConfidence ${pct}% — ${context.entity} vs ${context.match}:`);
    console.log(`  Routed: ${result.routedAction}`);
    console.log(`  Final:  ${result.finalAction}`);
    console.log(`  Human reviewed: ${result.humanReviewed}`);
    if (result.reviewResult) {
      console.log(`  Review: ${JSON.stringify(result.reviewResult)}`);
    }
  }

  const stats = gate.getStats();
  console.log(`\n${"=".repeat(60)}`);
  console.log("HITL Gate Stats:");
  console.log(`  Total decisions: ${stats.totalDecisions}`);
  console.log(`  Approved: ${stats.approved}`);
  console.log(`  Denied: ${stats.denied}`);
  console.log(`  Human reviewed: ${stats.humanReviewed}`);

  console.log("\n" + "=".repeat(60));
  console.log("All tests complete.");
  console.log("=".repeat(60));
}
