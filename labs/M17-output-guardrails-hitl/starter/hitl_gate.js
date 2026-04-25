/**
 * M17: HITL Approval Gate — Starter
 * Routes decisions by confidence level: auto-approve, human review, or auto-deny.
 * Domain context: UCC entity matching where partial matches need human verification.
 */
import * as readline from "readline";

// ── Confidence Thresholds ───────────────────────────────────
const AUTO_APPROVE_THRESHOLD = 0.9;
const HITL_REVIEW_THRESHOLD = 0.7;

/**
 * Route a decision based on confidence score.
 * @param {number} confidence - Float 0.0-1.0.
 * @param {Object} context - Match details.
 * @returns {{ action: string, reason: string, confidence: number, requiresHuman: boolean }}
 */
export function routeDecision(confidence, context) {
  // TODO 1: Implement confidence-based routing:
  // - confidence > AUTO_APPROVE_THRESHOLD -> action="approve", requiresHuman=false
  // - confidence >= HITL_REVIEW_THRESHOLD -> action="review", requiresHuman=true
  // - confidence < HITL_REVIEW_THRESHOLD -> action="deny", requiresHuman=false
  return {
    action: "review",
    reason: "Not yet implemented",
    confidence,
    requiresHuman: true,
  };
}

/**
 * Simulate human review of a decision.
 * @param {Object} context - Decision context.
 * @param {boolean} autoMode - If true, auto-approve (for tests).
 * @returns {Promise<{ approved: boolean, reviewer: string, notes: string }>}
 */
export async function simulateHumanReview(context, autoMode = true) {
  // TODO 2: If autoMode: return approved=true, reviewer="auto-test".
  // If not autoMode: use readline to prompt user for approval.
  return {
    approved: true,
    reviewer: "auto-test",
    notes: "Not yet implemented",
  };
}

export class HITLGate {
  /**
   * @param {boolean} autoMode - If true, simulate human approvals.
   */
  constructor(autoMode = true) {
    this.autoMode = autoMode;
    // TODO 3: Initialize tracking:
    //   this.decisions = [];
    //   this.reviewQueue = [];
    //   this.stats = { approved: 0, denied: 0, reviewed: 0 };
  }

  /**
   * Process a decision through the HITL gate.
   * @param {number} confidence
   * @param {Object} context
   * @returns {Promise<Object>}
   */
  async process(confidence, context) {
    // TODO 4: Use routeDecision() to get initial routing.
    // If action is "review", call simulateHumanReview().
    // Log to this.decisions and update this.stats.
    const routing = routeDecision(confidence, context);

    return {
      finalAction: routing.action !== "review" ? routing.action : "approve",
      routedAction: routing.action,
      confidence,
      humanReviewed: false,
      reviewResult: null,
    };
  }

  /** Return summary statistics. */
  getStats() {
    // TODO 5: Return stats with counts.
    return {
      totalDecisions: 0,
      approved: 0,
      denied: 0,
      humanReviewed: 0,
      decisions: [],
    };
  }

  /** Return pending reviews. */
  getPendingReviews() {
    // TODO 6: Return this.reviewQueue.
    return [];
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
  console.log("Self-test complete. Fill in TODOs for correct routing behavior.");
  console.log("=".repeat(60));
}
