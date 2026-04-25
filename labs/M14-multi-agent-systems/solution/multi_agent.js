/**
 * M14 Lab — Multi-Agent Systems (Solution)
 * ==========================================
 * Complete 4-agent pipeline with coordinator.
 *
 * Usage:
 *     node multi_agent.js
 */

import Anthropic from "@anthropic-ai/sdk";
import { config } from "dotenv";
import { dirname, join } from "path";
import { fileURLToPath } from "url";

config();
const __dirname = dirname(fileURLToPath(import.meta.url));
const { searchFilings, getFilingByNumber } = await import(join(__dirname, "..", "..", "shared", "mock_ucc_data.js"));

const client = new Anthropic();
const MODEL = "claude-sonnet-4-20250514";

function observe(label, msg) { console.log(`\n${"=".repeat(60)}\n[${label}] ${msg}\n${"=".repeat(60)}`); }
function observeAgent(name, action) { console.log(`\n${"─".repeat(60)}\n[AGENT: ${name}] ${action}\n${"─".repeat(60)}`); }
function observeHandoff(from, to, size) { console.log(`\n${"─".repeat(60)}\n[HANDOFF] ${from} → ${to} (${size} chars)\n${"─".repeat(60)}`); }

const RESEARCH_TOOLS = [
  { name: "search_filings", description: "Search UCC filings.", input_schema: { type: "object", properties: { debtor_name: { type: "string" }, state: { type: "string" } }, required: [] } },
  { name: "get_filing_details", description: "Get filing details.", input_schema: { type: "object", properties: { filing_number: { type: "string" } }, required: ["filing_number"] } },
];
const ANALYSIS_TOOLS = [
  { name: "calculate_risk", description: "Calculate risk.", input_schema: { type: "object", properties: { debtor_name: { type: "string" } }, required: ["debtor_name"] } },
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
    return JSON.stringify({ error: `Unknown: ${name}` });
  } catch (e) { return JSON.stringify({ error: e.message }); }
}

async function runSubagent(agentName, systemPrompt, task, tools = null, maxTurns = 5) {
  observeAgent(agentName, `Starting: ${task.slice(0, 100)}...`);
  const messages = [{ role: "user", content: task }];

  if (!tools || !tools.length) {
    const resp = await client.messages.create({ model: MODEL, max_tokens: 4096, system: systemPrompt, messages });
    const text = resp.content.filter(b => b.type === "text").map(b => b.text).join("");
    observeAgent(agentName, `Complete (${text.length} chars)`);
    return text;
  }

  for (let t = 0; t < maxTurns; t++) {
    const resp = await client.messages.create({ model: MODEL, max_tokens: 4096, system: systemPrompt, tools, messages });
    if (resp.stop_reason !== "tool_use") {
      const text = resp.content.filter(b => b.type === "text").map(b => b.text).join("");
      observeAgent(agentName, `Complete (${text.length} chars)`);
      return text;
    }
    const results = [];
    for (const b of resp.content) { if (b.type === "tool_use") results.push({ type: "tool_result", tool_use_id: b.id, content: executeTool(b.name, b.input) }); }
    messages.push({ role: "assistant", content: resp.content });
    messages.push({ role: "user", content: results });
  }
  return `${agentName} did not complete within ${maxTurns} turns.`;
}

async function runResearcher(task) {
  return runSubagent("Researcher", "You are a UCC filing researcher. Search for filings and report structured data: filing numbers, debtors, secured parties, states, collateral. Be thorough.", task, RESEARCH_TOOLS);
}

async function runAnalyst(task, researchData) {
  return runSubagent("Analyst", "You are a UCC filing analyst. Analyze research data, calculate risk scores, identify patterns in collateral breadth and lien concentration.", `${task}\n\n## Research Data\n${researchData}`, ANALYSIS_TOOLS);
}

async function runWriter(task, analysis) {
  return runSubagent("Writer", "You are a professional report writer. Create clear, well-structured reports with headers, bullet points, and recommendations.", `${task}\n\n## Analysis\n${analysis}\n\nWrite a professional report.`, null);
}

async function runReviewer(task, report) {
  return runSubagent("Reviewer", "You are a report reviewer. Check accuracy, completeness, clarity. Return the report with 'Review: APPROVED' if good, or note issues.", `Review this report:\n\nOriginal request: ${task}\n\n## Report\n${report}`, null);
}

async function runCoordinator(userQuery) {
  observe("COORDINATOR", `Received: ${userQuery}`);

  observe("COORDINATOR", "Phase 1: Researcher");
  const research = await runResearcher(userQuery);
  observeHandoff("Researcher", "Analyst", research.length);

  observe("COORDINATOR", "Phase 2: Analyst");
  const analysis = await runAnalyst(userQuery, research);
  observeHandoff("Analyst", "Writer", analysis.length);

  observe("COORDINATOR", "Phase 3: Writer");
  const report = await runWriter(userQuery, analysis);
  observeHandoff("Writer", "Reviewer", report.length);

  observe("COORDINATOR", "Phase 4: Reviewer");
  const final = await runReviewer(userQuery, report);

  observe("COORDINATOR", "Pipeline complete");
  return final;
}

console.log("=".repeat(60));
console.log("M14 Lab — Multi-Agent Systems (SOLUTION)");
console.log("=".repeat(60));

const r1 = await runCoordinator("Create a risk analysis report for Greenfield Logistics LLC");
console.log(`\nFINAL OUTPUT:\n${r1}`);

const r2 = await runCoordinator("Research and compare Nextera Holdings and Peachtree Ventures");
console.log(`\nFINAL OUTPUT:\n${r2}`);
