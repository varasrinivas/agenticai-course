/**
 * M13 Lab — Planning & Task Decomposition (Starter)
 * ===================================================
 * Build a planning agent that decomposes complex queries into
 * ordered sub-tasks, then executes each step using a ReAct loop.
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

// =============================================================================
// OBSERVATION HELPERS (complete — do not modify)
// =============================================================================

function observe(label, message) {
  console.log(`\n${"=".repeat(60)}`);
  console.log(`[${label}] ${message}`);
  console.log("=".repeat(60));
}

function observePlan(plan) {
  console.log(`\n${"=".repeat(60)}`);
  console.log("[PLAN] Decomposed into steps:");
  plan.forEach((step, i) => {
    const deps = step.depends_on || [];
    const depStr = deps.length ? ` (depends on: ${deps.join(", ")})` : "";
    console.log(`  ${i + 1}. ${step.task}${depStr}`);
  });
  console.log("=".repeat(60));
}

function observeStep(num, task) {
  console.log(`\n${"─".repeat(60)}`);
  console.log(`[STEP ${num}] Executing: ${task}`);
  console.log("─".repeat(60));
}

function observeStepResult(num, result) {
  console.log(`\n${"─".repeat(60)}`);
  console.log(`[STEP ${num} RESULT]`);
  console.log(result.length > 300 ? result.slice(0, 300) + "\n... (truncated)" : result);
  console.log("─".repeat(60));
}

// =============================================================================
// TOOLS (complete — do not modify)
// =============================================================================

const TOOLS = [
  { name: "search_filings", description: "Search UCC filings by debtor name and/or state.",
    input_schema: { type: "object", properties: { debtor_name: { type: "string" }, state: { type: "string" } }, required: [] } },
  { name: "get_filing_details", description: "Get full details of a specific UCC filing.",
    input_schema: { type: "object", properties: { filing_number: { type: "string" } }, required: ["filing_number"] } },
  { name: "calculate_risk", description: "Calculate risk profile for a debtor.",
    input_schema: { type: "object", properties: { debtor_name: { type: "string" } }, required: ["debtor_name"] } },
  { name: "generate_report_section", description: "Generate a report section from data.",
    input_schema: { type: "object", properties: { section_title: { type: "string" }, data: { type: "string" } }, required: ["section_title", "data"] } },
];

function calculateRiskForDebtor(name) {
  const filings = searchFilings({ debtorName: name });
  if (!filings.length) return { debtor: name, risk_score: 0, risk_level: "UNKNOWN" };
  const active = filings.filter(f => f.status === "Active");
  const blanket = filings.filter(f => f.collateral_description.toLowerCase().includes("all assets") || f.collateral_description.toLowerCase().includes("all accounts"));
  const amend = filings.filter(f => f.type === "UCC-3");
  const score = Math.min(1.0, active.length * 0.25 + blanket.length * 0.3 + amend.length * 0.1);
  const level = score >= 0.7 ? "HIGH" : score >= 0.4 ? "MEDIUM" : "LOW";
  return { debtor: name, risk_score: Math.round(score * 100) / 100, risk_level: level,
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
    } else if (name === "calculate_risk") {
      return JSON.stringify(calculateRiskForDebtor(input.debtor_name), null, 2);
    } else if (name === "generate_report_section") {
      return JSON.stringify({ section: input.section_title, content: `[Section generated]`, data_received: (input.data||"").slice(0,200)+"..." }, null, 2);
    }
    return JSON.stringify({ error: `Unknown tool: ${name}` });
  } catch (e) { return JSON.stringify({ error: e.message }); }
}

// =============================================================================
// PLANNING AGENT — YOUR CODE HERE
// =============================================================================

/**
 * Ask Claude to decompose a complex query into ordered sub-tasks.
 *
 * TODO 1: Implement this function
 *   - Call client.messages.create() with a planning system prompt
 *   - Parse the JSON plan from Claude's response
 *   - Return array of step objects: [{step_id, task, depends_on, tools_needed}]
 */
async function createPlan(userQuery) {
  // Your code here
  return [{ step_id: "step_1", task: userQuery, depends_on: [], tools_needed: ["search_filings"] }];
}

/**
 * Execute a single plan step using the ReAct loop.
 *
 * TODO 2: Implement this function
 *   - Build a system prompt with the step task and previous context
 *   - Run a ReAct loop (tool_use check → execute → loop)
 *   - Return the final text result
 */
async function executeStep(step, context, maxTurns = 5) {
  // Your code here
  return "TODO: Implement step execution";
}

/**
 * Run the full planning agent: plan → execute → synthesize.
 *
 * TODO 3: Implement this function
 *   - createPlan() to decompose the query
 *   - Loop through steps, calling executeStep() for each
 *   - Build cumulative context
 *   - Synthesize final result
 */
async function runPlanningAgent(userQuery) {
  observe("QUERY", userQuery);
  // Your code here
  return "TODO: Implement planning agent";
}

// =============================================================================
// MAIN
// =============================================================================

console.log("=".repeat(60));
console.log("M13 Lab — Planning & Task Decomposition");
console.log("=".repeat(60));

console.log("\n\n>>> Scenario 1: Generate risk report");
const r1 = await runPlanningAgent("Generate a complete risk report for Greenfield Logistics LLC");
console.log(`\nFINAL REPORT:\n${r1}`);

console.log("\n\n>>> Scenario 2: Compare two entities");
const r2 = await runPlanningAgent("Compare lien exposure between Nextera Holdings and Lone Star Energy");
console.log(`\nFINAL REPORT:\n${r2}`);
