/**
 * M18 Lab: LLM-as-Judge Evaluation Harness — SOLUTION (Node.js)
 * ==============================================================
 * Run: node llm_judge.js
 */

import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import OpenAI from "openai";

const client = new OpenAI({ baseURL: "http://localhost:11434/v1", apiKey: "ollama" });
const DATASET = join(dirname(fileURLToPath(import.meta.url)), "..", "starter", "eval_dataset.json");

const JUDGE_PROMPT = (question, answer, context) => `You are an impartial evaluator assessing the quality of an AI entity resolution agent's response. Score each dimension from 0.0 to 1.0.

QUESTION: ${question}

AGENT RESPONSE: ${answer}

RETRIEVED CONTEXT (what the agent had access to):
${context}

EVALUATION CRITERIA:
1. Reasoning quality (0-1): Does the agent reason step-by-step from evidence to conclusion?
2. Faithfulness (0-1): Does the answer use ONLY facts present in the retrieved context? Score 0 if it invents any fact not in context.
3. Evidence sufficiency (0-1): Did the agent use at least two independent pieces of evidence before reaching its confidence score?
4. Confidence calibration (0-1): Is the confidence score plausible given the evidence?

IMPORTANT:
- Do NOT favor longer or shorter answers — length does not equal quality.
- Base ALL scores on the criteria above, not on whether you agree with the final decision.
- Return ONLY valid JSON — no markdown, no explanation outside the JSON.

Return:
{
  "reasoning_quality": 0.0,
  "faithfulness": 0.0,
  "evidence_sufficiency": 0.0,
  "confidence_calibration": 0.0,
  "overall": 0.0,
  "explanation": "one sentence explaining the overall score"
}`;

const ZERO_SCORES = {
  reasoning_quality: 0, faithfulness: 0,
  evidence_sufficiency: 0, confidence_calibration: 0, overall: 0,
};

async function runJudge(question, answer, context, model = "mistral") {
  const ctxStr = context.map((c) => `- ${c}`).join("\n");
  try {
    const resp = await client.chat.completions.create({
      model,
      messages: [{ role: "user", content: JUDGE_PROMPT(question, answer, ctxStr) }],
      temperature: 0, // (mostly) deterministic judging
      max_tokens: 512,
    });
    let raw = (resp.choices[0].message.content ?? "").trim();
    raw = raw.replace(/^```(?:json)?\s*/, "").replace(/\s*```$/, "");
    return JSON.parse(raw);
  } catch (e) {
    // A broken judge must NOT silently pass cases
    return { ...ZERO_SCORES, explanation: String(e), judge_error: true };
  }
}

async function evaluateWithJudge(testCases, threshold = 0.7) {
  const results = [];
  for (const tc of testCases) {
    const scores = await runJudge(tc.question, tc.answer, tc.context);
    const passed = !scores.judge_error && (scores.overall ?? 0) >= threshold;
    results.push({ id: tc.id, scores, passed, overall: scores.overall ?? 0 });
    const status = passed ? "PASS" : "FAIL";
    console.log(`  [${status}] ${tc.id}: overall=${(scores.overall ?? 0).toFixed(2)} — ${scores.explanation ?? ""}`);
  }
  const passedCount = results.filter((r) => r.passed).length;
  return {
    results,
    pass_rate: results.length ? passedCount / results.length : 0,
    passed: passedCount,
    total: results.length,
  };
}

const cases = JSON.parse(readFileSync(DATASET, "utf-8")).cases;
console.log(`Loaded ${cases.length} eval cases\n`);
console.log("Running LLM-as-judge (3 judge calls, ~1 min on CPU)...");

const summary = await evaluateWithJudge(cases, 0.7);

console.log(`\nPass rate: ${summary.passed}/${summary.total} (${Math.round(summary.pass_rate * 100)}%)`);
console.log("\nExpected: good-merge PASSES, hallucinated-merge FAILS.");
console.log("honest-uncertainty is contested — judges often under-score honest refusals.");
