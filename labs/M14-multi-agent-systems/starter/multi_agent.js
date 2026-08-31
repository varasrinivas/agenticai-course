/**
 * M14 Lab — Multi-Agent Systems (Starter)
 * =========================================
 * Build a 4-agent content pipeline coordinated by a supervisor.
 *
 * KEY CONCEPT: Each subagent has its OWN system prompt and conversation.
 * Context is passed EXPLICITLY — subagents don't inherit the coordinator's history.
 *
 * Usage:
 *     node multi_agent.js
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
function observeAgent(name, action) { console.log(`\n${"─".repeat(60)}\n[AGENT: ${name}] ${action}\n${"─".repeat(60)}`); }
function observeHandoff(from, to, size) { console.log(`\n${"─".repeat(60)}\n[HANDOFF] ${from} → ${to} (${size} chars)\n${"─".repeat(60)}`); }

const RESEARCH_TOOLS = [
  { name: "search_filings", description: "Search UCC filings by debtor name/state.", input_schema: { type: "object", properties: { debtor_name: { type: "string" }, state: { type: "string" } }, required: [] } },
  { name: "get_filing_details", description: "Get full filing details.", input_schema: { type: "object", properties: { filing_number: { type: "string" } }, required: ["filing_number"] } },
];

const ANALYSIS_TOOLS = [
  { name: "calculate_risk", description: "Calculate risk profile for a debtor.", input_schema: { type: "object", properties: { debtor_name: { type: "string" } }, required: ["debtor_name"] } },
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
    return JSON.stringify({ error: `Unknown tool: ${name}` });
  } catch (e) { return JSON.stringify({ error: e.message }); }
}

// =============================================================================
// YOUR CODE HERE
// =============================================================================

/**
 * TODO 1: Implement runSubagent() — runs a specialist agent with isolated context
 * TODO 2: Implement runResearcher(), runAnalyst(), runWriter(), runReviewer()
 * TODO 3: Implement runCoordinator() — orchestrates the pipeline
 */

async function runSubagent(agentName, systemPrompt, task, tools = null, maxTurns = 5) {
  observeAgent(agentName, `Starting: ${task.slice(0, 100)}...`);
  // Your code here
  return "TODO: Implement subagent runner";
}

async function runCoordinator(userQuery) {
  observe("COORDINATOR", `Received: ${userQuery}`);
  // Your code here — call researcher → analyst → writer → reviewer
  return "TODO: Implement coordinator";
}

// =============================================================================
// MAIN
// =============================================================================

console.log("=".repeat(60));
console.log("M14 Lab — Multi-Agent Systems");
console.log("=".repeat(60));

const r1 = await runCoordinator("Create a risk analysis report for Greenfield Logistics LLC");
console.log(`\nFINAL OUTPUT:\n${r1}`);

const r2 = await runCoordinator("Research and compare Nextera Holdings and Peachtree Ventures");
console.log(`\nFINAL OUTPUT:\n${r2}`);
