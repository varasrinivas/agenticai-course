/**
 * M18 — Eval Runner (Node.js Solution)
 * Orchestrates the full evaluation pipeline.
 */

import fs from "fs";
import { EVAL_CASES, MOCK_AGENT_RESPONSES, getSummary } from "./eval_dataset.js";
import { scoreTaskCompletion } from "./task_scorer.js";
import { scoreEntityResolution } from "./fuzzy_scorer.js";
import { scoreWithJudge } from "./judge_scorer.js";
import { fileURLToPath } from "url";

/**
 * Mock agent function that returns predetermined responses.
 */
function mockAgentFn(query, caseId = null) {
  if (caseId && MOCK_AGENT_RESPONSES[caseId]) {
    return MOCK_AGENT_RESPONSES[caseId];
  }
  return "I was unable to find any relevant information for your query.";
}

class EvalRunner {
  constructor(mockMode = true) {
    this.mockMode = mockMode;
    this.results = [];
  }

  /**
   * Run all test cases through the agent and score them.
   */
  async runEval(cases, agentFn = null, mockMode = null) {
    agentFn = agentFn || mockAgentFn;
    mockMode = mockMode !== null ? mockMode : this.mockMode;
    this.results = [];

    for (let i = 0; i < cases.length; i++) {
      const c = cases[i];
      const response = agentFn(c.query, c.id);

      const taskResult = scoreTaskCompletion(response, c.expected);
      const entityResult = scoreEntityResolution(response, c.expected);
      const judgeResult = await scoreWithJudge(
        c.query,
        response,
        c.expected,
        mockMode
      );

      const overall =
        (taskResult.score + entityResult.score + judgeResult.score) / 3.0;

      const result = {
        case_id: c.id,
        category: c.category,
        difficulty: c.difficulty,
        query: c.query,
        response,
        task_score: taskResult,
        entity_score: entityResult,
        judge_score: judgeResult,
        overall_score: Math.round(overall * 1000) / 1000,
        passed: overall >= 0.6,
      };

      this.results.push(result);
      const status = result.passed ? "PASS" : "FAIL";
      const idx = String(i + 1).padStart(2, " ");
      console.log(
        `  [${idx}/${cases.length}] ${c.id.padEnd(6)} ${status}  ` +
          `task=${taskResult.score.toFixed(2)}  ` +
          `entity=${entityResult.score.toFixed(2)}  ` +
          `judge=${judgeResult.score.toFixed(2)}  ` +
          `overall=${overall.toFixed(2)}`
      );
    }

    return this.results;
  }

  /**
   * Generate a formatted evaluation report.
   */
  generateReport(results = null) {
    results = results || this.results;
    if (!results.length) return "No results to report.";

    const now = new Date().toISOString();
    const runId = `eval-${now.replace(/[:.]/g, "").slice(0, 15)}`;
    const total = results.length;
    const passed = results.filter((r) => r.passed).length;
    const failed = total - passed;
    const avgScore = results.reduce((s, r) => s + r.overall_score, 0) / total;
    const avgTask = results.reduce((s, r) => s + r.task_score.score, 0) / total;
    const avgEntity = results.reduce((s, r) => s + r.entity_score.score, 0) / total;
    const avgJudge = results.reduce((s, r) => s + r.judge_score.score, 0) / total;

    const lines = [];
    lines.push("");
    lines.push("=".repeat(55));
    lines.push("  UCC Research Agent — Evaluation Report");
    lines.push("=".repeat(55));
    lines.push(`  Run ID:    ${runId}`);
    lines.push(`  Date:      ${now}`);
    lines.push(`  Cases:     ${total}  |  Pass: ${passed}  |  Fail: ${failed}`);
    lines.push(`  Overall:   ${avgScore.toFixed(3)}`);
    lines.push(`  Threshold: 0.600 (pass/fail cutoff)`);
    lines.push("");

    lines.push("-".repeat(55));
    lines.push("  Scorer Averages");
    lines.push("-".repeat(55));
    lines.push(`  ${"Scorer".padEnd(25)} ${"Avg Score".padStart(10)}`);
    lines.push(`  ${"─".repeat(25)} ${"─".repeat(10)}`);
    lines.push(`  ${"Task Completion".padEnd(25)} ${avgTask.toFixed(3).padStart(10)}`);
    lines.push(`  ${"Entity Resolution".padEnd(25)} ${avgEntity.toFixed(3).padStart(10)}`);
    lines.push(`  ${"Claude-as-Judge".padEnd(25)} ${avgJudge.toFixed(3).padStart(10)}`);
    lines.push("");

    // Per-category
    const categories = {};
    for (const r of results) {
      if (!categories[r.category]) categories[r.category] = [];
      categories[r.category].push(r);
    }

    lines.push("-".repeat(55));
    lines.push("  Per-Category Breakdown");
    lines.push("-".repeat(55));
    lines.push(
      `  ${"Category".padEnd(25)} ${"Cases".padStart(6)} ${"Pass".padStart(6)} ${"Avg".padStart(8)}`
    );
    lines.push(`  ${"─".repeat(25)} ${"─".repeat(6)} ${"─".repeat(6)} ${"─".repeat(8)}`);

    for (const cat of Object.keys(categories).sort()) {
      const cr = categories[cat];
      const ct = cr.length;
      const cp = cr.filter((r) => r.passed).length;
      const ca = cr.reduce((s, r) => s + r.overall_score, 0) / ct;
      lines.push(
        `  ${cat.padEnd(25)} ${String(ct).padStart(6)} ${String(cp).padStart(6)} ${ca.toFixed(3).padStart(8)}`
      );
    }
    lines.push("");

    // Worst performers
    const sorted = [...results].sort((a, b) => a.overall_score - b.overall_score);
    const worst = sorted.slice(0, 3);

    lines.push("-".repeat(55));
    lines.push("  Worst Performing Cases");
    lines.push("-".repeat(55));
    for (const r of worst) {
      lines.push(
        `  ${r.case_id.padEnd(6)}  score=${r.overall_score.toFixed(3)}  (${r.category}, ${r.difficulty})`
      );
      lines.push(`         query: ${r.query.slice(0, 50)}...`);
    }
    lines.push("");
    lines.push("=".repeat(55));

    return lines.join("\n");
  }

  /**
   * Save results to JSON file.
   */
  saveResults(results = null, filepath = null) {
    results = results || this.results;
    if (!filepath) {
      const ts = new Date().toISOString().replace(/[:.]/g, "").slice(0, 15);
      filepath = `eval_results_${ts}.json`;
    }

    const total = results.length;
    const passed = results.filter((r) => r.passed).length;
    const avgScore = results.reduce((s, r) => s + r.overall_score, 0) / total;

    const saveData = {
      timestamp: new Date().toISOString(),
      summary: { total, passed, failed: total - passed, average_score: Math.round(avgScore * 1000) / 1000 },
      results: results.map((r) => ({
        case_id: r.case_id,
        category: r.category,
        difficulty: r.difficulty,
        overall_score: r.overall_score,
        task_score: r.task_score.score,
        entity_score: r.entity_score.score,
        judge_score: r.judge_score.score,
        passed: r.passed,
      })),
    };

    fs.writeFileSync(filepath, JSON.stringify(saveData, null, 2));
    return filepath;
  }

  /**
   * Compare two eval runs.
   */
  compareRuns(current, previous) {
    const currScores = {};
    for (const r of current) currScores[r.case_id] = r.overall_score;
    const prevScores = {};
    for (const r of previous) prevScores[r.case_id] = r.overall_score;

    const improvements = [];
    const regressions = [];
    let unchanged = 0;

    for (const caseId of Object.keys(currScores)) {
      if (!(caseId in prevScores)) continue;
      const diff = currScores[caseId] - prevScores[caseId];
      if (diff > 0.05) improvements.push({ caseId, prev: prevScores[caseId], curr: currScores[caseId], diff });
      else if (diff < -0.05) regressions.push({ caseId, prev: prevScores[caseId], curr: currScores[caseId], diff });
      else unchanged++;
    }

    const currAvg = Object.values(currScores).reduce((a, b) => a + b, 0) / Object.values(currScores).length;
    const prevAvg = Object.values(prevScores).reduce((a, b) => a + b, 0) / Object.values(prevScores).length;

    const lines = [];
    lines.push("");
    lines.push("-".repeat(55));
    lines.push("  Regression Comparison");
    lines.push("-".repeat(55));
    lines.push(`  Previous avg: ${prevAvg.toFixed(3)}`);
    lines.push(`  Current avg:  ${currAvg.toFixed(3)}`);
    lines.push(`  Change:       ${(currAvg - prevAvg) >= 0 ? "+" : ""}${(currAvg - prevAvg).toFixed(3)}`);
    lines.push("");

    if (regressions.length) {
      lines.push(`  REGRESSIONS (${regressions.length}):`);
      for (const r of regressions.sort((a, b) => a.diff - b.diff)) {
        lines.push(`    ${r.caseId}: ${r.prev.toFixed(3)} -> ${r.curr.toFixed(3)} (${r.diff >= 0 ? "+" : ""}${r.diff.toFixed(3)})`);
      }
    } else {
      lines.push("  No regressions detected.");
    }

    if (improvements.length) {
      lines.push(`\n  IMPROVEMENTS (${improvements.length}):`);
      for (const r of improvements.sort((a, b) => b.diff - a.diff)) {
        lines.push(`    ${r.caseId}: ${r.prev.toFixed(3)} -> ${r.curr.toFixed(3)} (+${r.diff.toFixed(3)})`);
      }
    }

    lines.push(`\n  Unchanged: ${unchanged} cases`);
    lines.push("-".repeat(55));
    return lines.join("\n");
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
