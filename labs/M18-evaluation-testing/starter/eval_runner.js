/**
 * M18 — Eval Runner (Node.js Starter)
 * Orchestrates the full evaluation pipeline.
 *
 * TODO: Implement the EvalRunner class and mockAgentFn.
 */

import fs from "fs";

// NOTE: loads eval_dataset.js from starter/ once you have copied it there, and
// falls back to the solution/ copy until then.
//
// await import(), not require(): labs/package.json declares "type": "module",
// so require is not defined in this file at all. A static import would not work
// either — it cannot be wrapped in try/catch, and tolerating a missing first
// path is the whole point of this block.
let EVAL_CASES, MOCK_AGENT_RESPONSES, getSummary;
try {
  ({ EVAL_CASES, MOCK_AGENT_RESPONSES, getSummary } = await import("./eval_dataset.js"));
} catch {
  // Fallback: the solution directory's copy
  ({ EVAL_CASES, MOCK_AGENT_RESPONSES, getSummary } = await import("../solution/eval_dataset.js"));
}
import { scoreTaskCompletion } from "./task_scorer.js";
import { scoreEntityResolution } from "./fuzzy_scorer.js";
import { scoreWithJudge } from "./judge_scorer.js";
import { fileURLToPath } from "url";

/**
 * Mock agent function that returns predetermined responses.
 *
 * TODO:
 * 1. Look up MOCK_AGENT_RESPONSES[caseId]
 * 2. Return generic message if not found
 *
 * @param {string} query
 * @param {string|null} caseId
 * @returns {string}
 */
function mockAgentFn(query, caseId = null) {
  // TODO: Implement mock agent lookup
  return "";
}

class EvalRunner {
  constructor(mockMode = true) {
    this.mockMode = mockMode;
    this.results = [];
  }

  /**
   * Run all test cases through the agent and score them.
   *
   * TODO:
   * 1. For each case, call agentFn(query, caseId)
   * 2. Score with all 3 scorers
   * 3. Calculate overall = average of 3 scores
   * 4. Mark passed if overall >= 0.6
   * 5. Return results array
   */
  async runEval(cases, agentFn = null, mockMode = null) {
    // TODO: Implement eval loop
    return [];
  }

  /**
   * Generate a formatted evaluation report.
   *
   * TODO:
   * 1. Calculate aggregate stats
   * 2. Per-category and per-difficulty breakdowns
   * 3. Find worst performing cases
   * 4. Format into readable string
   */
  generateReport(results = null) {
    // TODO: Implement report generation
    return "Report not implemented yet.";
  }

  /**
   * Save results to JSON for regression comparison.
   *
   * TODO: Serialize results with timestamp and summary stats
   */
  saveResults(results = null, filepath = null) {
    // TODO: Implement save
    return "eval_results.json";
  }

  /**
   * Compare two eval runs and highlight regressions.
   *
   * TODO:
   * 1. Build score lookups for both runs
   * 2. Find improvements, regressions, unchanged
   * 3. Format comparison report
   */
  compareRuns(current, previous) {
    // TODO: Implement comparison
    return "Comparison not implemented yet.";
  }
}

// ---------------------------------------------------------------------------
// Self-test
// ---------------------------------------------------------------------------
// ESM has no require.main; compare the resolved entry path instead.
if (process.argv[1] === fileURLToPath(import.meta.url)) {
  (async () => {
    console.log("M18 Eval Runner — Full Pipeline Test (Node.js)");
    console.log("=".repeat(60));

    const summary = getSummary();
    console.log(`\nDataset: ${summary.total_cases} cases`);

    console.log("\nRunning evaluation...");
    const runner = new EvalRunner(true);
    const results = await runner.runEval(EVAL_CASES, mockAgentFn);

    const report = runner.generateReport(results);
    console.log(report);

    const filepath = runner.saveResults(results);
    console.log(`\nResults saved to: ${filepath}`);
  })();
}

export { EvalRunner, mockAgentFn };
