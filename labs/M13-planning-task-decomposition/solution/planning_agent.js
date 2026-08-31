/**
 * M13 Lab — Planning & Task Decomposition (Solution)
 * ====================================================
 * Complete planning agent with decomposition, step execution, and synthesis.
 *
 * Usage:
 *     node planning_agent.js
 */

import Anthropic from "@anthropic-ai/sdk";
import { config } from "dotenv";
import { dirname, join } from "path";
import { fileURLToPath, pathToFileURL } from "url";

config();

const __dirname = dirname(fileURLToPath(import.meta.url));
// pathToFileURL: ESM import() needs a file:// URL, not a filesystem path.
// A bare Windows path (D:\...) is read as protocol 'd:' and rejected with
// ERR_UNSUPPORTED_ESM_URL_SCHEME. Posix paths happen to work, which is why
// this only breaks on Windows.
const { searchFilings, getFilingByNumber } = await import(pathToFileURL(join(__dirname, "..", "..", "shared", "mock_ucc_data.js")).href);

const client = new Anthropic();
const MODEL = "claude-sonnet-4-6";

function observe(label, msg) { console.log(`\n${"=".repeat(60)}\n[${label}] ${msg}\n${"=".repeat(60)}`); }
function observePlan(plan) {
  console.log(`\n${"=".repeat(60)}\n[PLAN] Decomposed into steps:`);
  plan.forEach((s, i) => { const d = (s.depends_on||[]).length ? ` (depends on: ${s.depends_on.join(", ")})` : ""; console.log(`  ${i+1}. ${s.task}${d}`); });
  console.log("=".repeat(60));
}
function observeStep(n, t) { console.log(`\n${"─".repeat(60)}\n[STEP ${n}] Executing: ${t}\n${"─".repeat(60)}`); }
function observeStepResult(n, r) { console.log(`\n${"─".repeat(60)}\n[STEP ${n} RESULT]\n${r.length > 300 ? r.slice(0,300)+"..." : r}\n${"─".repeat(60)}`); }

const TOOLS = [
  { name: "search_filings", description: "Search UCC filings by debtor name and/or state.", input_schema: { type: "object", properties: { debtor_name: { type: "string" }, state: { type: "string" } }, required: [] } },
  { name: "get_filing_details", description: "Get full details of a UCC filing.", input_schema: { type: "object", properties: { filing_number: { type: "string" } }, required: ["filing_number"] } },
  { name: "calculate_risk", description: "Calculate risk profile for a debtor.", input_schema: { type: "object", properties: { debtor_name: { type: "string" } }, required: ["debtor_name"] } },
  { name: "generate_report_section", description: "Generate a report section.", input_schema: { type: "object", properties: { section_title: { type: "string" }, data: { type: "string" } }, required: ["section_title", "data"] } },
];

function calculateRiskForDebtor(name) {
  const filings = searchFilings({ debtorName: name });
  if (!filings.length) return { debtor: name, risk_score: 0, risk_level: "UNKNOWN" };
  const active = filings.filter(f => f.status === "Active");
  const blanket = filings.filter(f => f.collateral_description.toLowerCase().includes("all assets") || f.collateral_description.toLowerCase().includes("all accounts"));
  const amend = filings.filter(f => f.type === "UCC-3");
  const score = Math.min(1.0, active.length * 0.25 + blanket.length * 0.3 + amend.length * 0.1);
  return { debtor: name, risk_score: Math.round(score*100)/100, risk_level: score >= 0.7 ? "HIGH" : score >= 0.4 ? "MEDIUM" : "LOW",
    total_filings: filings.length, active_filings: active.length, blanket_liens: blanket.length, amendments: amend.length };
}

function executeTool(name, input) {
  try {
    if (name === "search_filings") {
      const r = searchFilings({ debtorName: input.debtor_name, state: input.state });
      return JSON.stringify(r.map(f => ({ filing_number: f.filing_number, debtor: f.debtor.name, secured_party: f.secured_party.name, state: f.state, status: f.status, type: f.type, collateral: f.collateral_description.slice(0,120)+"..." })), null, 2);
    } else if (name === "get_filing_details") {
      const f = getFilingByNumber(input.filing_number);
      return f ? JSON.stringify(f, null, 2) : JSON.stringify({ error: "Not found" });
    } else if (name === "calculate_risk") { return JSON.stringify(calculateRiskForDebtor(input.debtor_name), null, 2); }
    else if (name === "generate_report_section") { return JSON.stringify({ section: input.section_title, content: "[Generated]", data_received: (input.data||"").slice(0,200)+"..." }, null, 2); }
    return JSON.stringify({ error: `Unknown tool: ${name}` });
  } catch (e) { return JSON.stringify({ error: e.message }); }
}

const PLANNING_PROMPT = `You are a task planning agent. Given a complex query about UCC filings, decompose it into 3-6 ordered steps.
Return ONLY a JSON array. Each step: {"step_id":"step_N","task":"...","depends_on":[],"tools_needed":["..."]}
Available tools: search_filings, get_filing_details, calculate_risk, generate_report_section`;

async function createPlan(userQuery) {
  const resp = await client.messages.create({ model: MODEL, max_tokens: 2048, system: PLANNING_PROMPT, messages: [{ role: "user", content: userQuery }] });
  let text = resp.content.filter(b => b.type === "text").map(b => b.text).join("").trim();
  if (text.startsWith("```")) { text = text.split("\n", 2)[1]; text = text.replace(/```\s*$/, ""); }
  try { const plan = JSON.parse(text); if (Array.isArray(plan) && plan.length) return plan; } catch {}
  return [{ step_id: "step_1", task: userQuery, depends_on: [], tools_needed: ["search_filings"] }];
}

async function executeStep(step, context, maxTurns = 5) {
  const system = `You are executing one step of a research plan about UCC filings.\n\n## Your Task\n${step.task}\n\n## Context From Previous Steps\n${context || "This is the first step."}\n\nUse tools as needed. Be concise.`;
  const messages = [{ role: "user", content: `Execute: ${step.task}` }];
  for (let t = 0; t < maxTurns; t++) {
    const resp = await client.messages.create({ model: MODEL, max_tokens: 2048, system, tools: TOOLS, messages });
    if (resp.stop_reason !== "tool_use") return resp.content.filter(b => b.type === "text").map(b => b.text).join("");
    const results = [];
    for (const b of resp.content) { if (b.type === "tool_use") results.push({ type: "tool_result", tool_use_id: b.id, content: executeTool(b.name, b.input) }); }
    messages.push({ role: "assistant", content: resp.content });
    messages.push({ role: "user", content: results });
  }
  return "Step did not complete.";
}

async function runPlanningAgent(userQuery) {
  observe("QUERY", userQuery);
  const plan = await createPlan(userQuery);
  observePlan(plan);

  const stepResults = {};
  let context = "";
  for (let i = 0; i < plan.length; i++) {
    const step = plan[i];
    observeStep(i + 1, step.task);
    const result = await executeStep(step, context);
    observeStepResult(i + 1, result);
    stepResults[step.step_id] = result;
    context += `\n\n--- Step ${i + 1}: ${step.task} ---\n${result}`;
  }

  if (plan.length > 1) {
    const synth = await client.messages.create({ model: MODEL, max_tokens: 4096, system: "Synthesize research results into a clear report.",
      messages: [{ role: "user", content: `Query: ${userQuery}\n\nResults:\n${context}\n\nSynthesize into a final report.` }] });
    const final = synth.content.filter(b => b.type === "text").map(b => b.text).join("");
    observe("FINAL REPORT", final.slice(0, 200) + (final.length > 200 ? "..." : ""));
    return final;
  }
  return stepResults.step_1 || "No results.";
}

console.log("=".repeat(60));
console.log("M13 Lab — Planning & Task Decomposition (SOLUTION)");
console.log("=".repeat(60));

const r1 = await runPlanningAgent("Generate a complete risk report for Greenfield Logistics LLC");
console.log(`\nFINAL REPORT:\n${r1}`);

const r2 = await runPlanningAgent("Compare lien exposure between Nextera Holdings and Lone Star Energy");
console.log(`\nFINAL REPORT:\n${r2}`);
