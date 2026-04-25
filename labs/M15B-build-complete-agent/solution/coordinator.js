/**
 * M15B — Coordinator + Subagents (Solution — Node.js)
 * =====================================================
 *
 * Usage:
 *     node coordinator.js
 */

import Anthropic from "@anthropic-ai/sdk";
import { config } from "dotenv";

config();

const client = new Anthropic();
const MODEL = "claude-sonnet-4-20250514";

// Inline mock data (same 15 filings)
const MOCK_FILINGS = [
  { filing_number: "UCC-2024-NY-0012847", type: "UCC-1", state: "New York", status: "Active", debtor: { name: "Acme Corporation" }, secured_party: { name: "Atlantic Capital Partners" }, collateral_description: "All accounts receivable, inventory, equipment, and general intangibles now owned or hereafter acquired." },
  { filing_number: "UCC-2024-NY-0015921", type: "UCC-1", state: "New York", status: "Active", debtor: { name: "Acme Corporation" }, secured_party: { name: "Citibank N.A." }, collateral_description: "All deposit accounts, investment property, and letter-of-credit rights." },
  { filing_number: "UCC-2023-NY-0145678", type: "UCC-3", state: "New York", status: "Terminated", debtor: { name: "Harbor Shipping International Inc" }, secured_party: { name: "Citibank N.A." }, collateral_description: "TERMINATION." },
  { filing_number: "UCC-2024-NY-0019004", type: "UCC-1", state: "New York", status: "Active", debtor: { name: "Greenfield Logistics LLC" }, secured_party: { name: "JPMorgan Chase Bank N.A." }, collateral_description: "All inventory and accounts receivable." },
  { filing_number: "UCC-2024-CA-0098231", type: "UCC-1", state: "California", status: "Active", debtor: { name: "Pacific Ridge Technologies Inc" }, secured_party: { name: "Silicon Valley Bank" }, collateral_description: "All assets including IP, patents, trademarks, accounts." },
  { filing_number: "UCC-2024-CA-0101457", type: "UCC-1", state: "California", status: "Active", debtor: { name: "Acme Corporation" }, secured_party: { name: "Bank of America N.A." }, collateral_description: "All equipment and fixtures." },
  { filing_number: "UCC-2023-CA-0087652", type: "UCC-3", state: "California", status: "Amendment", debtor: { name: "Pacific Ridge Technologies Inc" }, secured_party: { name: "Silicon Valley Bank" }, collateral_description: "Amendment to add software and SaaS contracts." },
  { filing_number: "UCC-2023-TX-0187634", type: "UCC-1", state: "Texas", status: "Active", debtor: { name: "Lone Star Energy Solutions LP" }, secured_party: { name: "Wells Fargo Equipment Finance" }, collateral_description: "Specific equipment: Caterpillar excavators and Liebherr crane." },
  { filing_number: "UCC-2024-TX-0201337", type: "UCC-1", state: "Texas", status: "Active", debtor: { name: "Acme Corporation" }, secured_party: { name: "PNC Bank N.A." }, collateral_description: "All accounts receivable from Texas operations." },
  { filing_number: "UCC-2024-TX-0215890", type: "UCC-1", state: "Texas", status: "Active", debtor: { name: "Lone Star Energy Solutions LP" }, secured_party: { name: "Caterpillar Financial Services Corp" }, collateral_description: "Specific equipment: Caterpillar D10T2 tractors." },
  { filing_number: "UCC-2024-FL-0054219", type: "UCC-3", state: "Florida", status: "Amendment", debtor: { name: "Sunshine Medical Group PA" }, secured_party: { name: "TD Bank N.A." }, collateral_description: "Amendment to add MRI systems and CT scanner." },
  { filing_number: "UCC-2024-FL-0059811", type: "UCC-1", state: "Florida", status: "Active", debtor: { name: "Acme Corporation" }, secured_party: { name: "Atlantic Capital Partners" }, collateral_description: "All accounts receivable, inventory of Florida division." },
  { filing_number: "UCC-2024-IL-0076543", type: "UCC-1", state: "Illinois", status: "Active", debtor: { name: "Midwest Agricultural Cooperative" }, secured_party: { name: "Farm Credit Services of America" }, collateral_description: "All farm products, crops, livestock, equipment." },
  { filing_number: "UCC-2024-IL-0081290", type: "UCC-1", state: "Illinois", status: "Active", debtor: { name: "Acme Corporation" }, secured_party: { name: "JPMorgan Chase Bank N.A." }, collateral_description: "All assets of Illinois subsidiary." },
  { filing_number: "UCC-2023-IL-0069221", type: "UCC-3", state: "Illinois", status: "Amendment", debtor: { name: "Midwest Agricultural Cooperative" }, secured_party: { name: "Farm Credit Services of America" }, collateral_description: "Amendment to add grain equipment and John Deere combines." },
];

function searchFilings({ debtorName, state } = {}) {
  let r = MOCK_FILINGS;
  if (debtorName) r = r.filter(f => f.debtor.name.toLowerCase().includes(debtorName.toLowerCase()));
  if (state) r = r.filter(f => f.state.toLowerCase() === state.toLowerCase());
  return r;
}
function getFilingByNumber(num) { return MOCK_FILINGS.find(f => f.filing_number === num) || null; }
function calculateRisk(name) {
  const filings = searchFilings({ debtorName: name });
  if (!filings.length) return { debtor: name, risk_score: 0, risk_level: "UNKNOWN" };
  const active = filings.filter(f => f.status === "Active");
  const blanket = filings.filter(f => f.collateral_description.toLowerCase().includes("all a"));
  const amend = filings.filter(f => f.type === "UCC-3");
  const states = [...new Set(filings.map(f => f.state))];
  const parties = [...new Set(filings.map(f => f.secured_party.name))];
  const score = Math.min(1.0, Math.round((active.length * 0.15 + blanket.length * 0.2 + amend.length * 0.05 + (states.length > 1 ? 0.1 : 0) + (parties.length > 1 ? 0.1 : 0)) * 100) / 100);
  return { debtor: name, risk_score: score, risk_level: score >= 0.7 ? "HIGH" : score >= 0.4 ? "MEDIUM" : "LOW", total_filings: filings.length, active_filings: active.length };
}

const SEARCH_TOOLS = [
  { name: "search_filings", description: "Search UCC filings.", input_schema: { type: "object", properties: { debtor_name: { type: "string" }, state: { type: "string" } }, required: [] } },
  { name: "get_filing_details", description: "Get filing details.", input_schema: { type: "object", properties: { filing_number: { type: "string" } }, required: ["filing_number"] } },
];
const RISK_TOOLS = [
  { name: "calculate_risk_score", description: "Calculate risk.", input_schema: { type: "object", properties: { debtor_name: { type: "string" } }, required: ["debtor_name"] } },
  { name: "search_filings", description: "Search filings for context.", input_schema: { type: "object", properties: { debtor_name: { type: "string" }, state: { type: "string" } }, required: [] } },
];

function executeTool(name, input) {
  if (name === "search_filings") { const r = searchFilings({ debtorName: input.debtor_name, state: input.state }); return !r.length ? JSON.stringify({ message: "No filings found" }) : JSON.stringify(r.map(f => ({ filing_number: f.filing_number, debtor: f.debtor.name, secured_party: f.secured_party.name, state: f.state, status: f.status, collateral: f.collateral_description.slice(0,120)+"..." })), null, 2); }
  if (name === "get_filing_details") { const f = getFilingByNumber(input.filing_number); return f ? JSON.stringify(f, null, 2) : JSON.stringify({ error: "Not found" }); }
  if (name === "calculate_risk_score") return JSON.stringify(calculateRisk(input.debtor_name), null, 2);
  return JSON.stringify({ error: `Unknown: ${name}` });
}

function observe(l, m) { console.log(`\n${"=".repeat(60)}\n[${l}] ${m}\n${"=".repeat(60)}`); }
function observeAgent(n, a) { console.log(`\n${"─".repeat(60)}\n[AGENT: ${n}] ${a}\n${"─".repeat(60)}`); }
function observeHandoff(f, t, s) { console.log(`\n${"─".repeat(60)}\n[HANDOFF] ${f} → ${t} (${s} chars)\n${"─".repeat(60)}`); }

async function runSubagent(name, system, task, tools, maxTurns = 6) {
  observeAgent(name, `Starting: ${task.slice(0, 100)}...`);
  const messages = [{ role: "user", content: task }];
  for (let t = 0; t < maxTurns; t++) {
    const resp = await client.messages.create({ model: MODEL, max_tokens: 4096, system, tools, messages });
    if (resp.stop_reason !== "tool_use") { const text = resp.content.filter(b => b.type === "text").map(b => b.text).join(""); observeAgent(name, `Complete (${text.length} chars)`); return text; }
    const results = [];
    for (const b of resp.content) { if (b.type === "tool_use") results.push({ type: "tool_result", tool_use_id: b.id, content: executeTool(b.name, b.input) }); }
    messages.push({ role: "assistant", content: resp.content });
    messages.push({ role: "user", content: results });
  }
  return `${name} did not complete.`;
}

class Coordinator {
  constructor() { this.history = []; }

  async run(query) {
    observe("COORDINATOR", `Received: ${query}`);
    this.history.push({ role: "user", content: query });
    const histCtx = this.history.slice(-10).map(e => `**${e.role === "user" ? "User" : "Assistant"}**: ${e.content.slice(0,200)}`).join("\n");
    const q = query.toLowerCase();
    const needsRisk = ["risk", "exposure", "assess", "evaluate"].some(w => q.includes(w));
    const needsSearch = ["find", "search", "filing", "what about"].some(w => q.includes(w));
    const taskCtx = `${query}\n\n## Previous Conversation\n${histCtx}`;

    let filingResults = null, riskResults = null;
    if (!needsRisk || (needsSearch && needsRisk) || (!needsSearch && !needsRisk)) {
      filingResults = await runSubagent("Filing Search", "You are a UCC filing search specialist. Search and retrieve filings. Be thorough.", taskCtx, SEARCH_TOOLS);
      observeHandoff("Filing Search", "Coordinator", filingResults.length);
    }
    if (needsRisk || (!needsSearch && !needsRisk)) {
      const riskTask = filingResults ? `${taskCtx}\n\n## Filing Data\n${filingResults}` : taskCtx;
      riskResults = await runSubagent("Risk Analysis", "You are a risk analysis specialist. Calculate and explain lien risk.", riskTask, RISK_TOOLS);
      observeHandoff("Risk Analysis", "Coordinator", riskResults.length);
    }

    const parts = [`User query: ${query}`];
    if (filingResults) parts.push(`## Filing Results\n${filingResults}`);
    if (riskResults) parts.push(`## Risk Results\n${riskResults}`);
    const synth = await client.messages.create({ model: MODEL, max_tokens: 4096, system: "Synthesize UCC research results. Cite filing numbers.", messages: [{ role: "user", content: parts.join("\n\n") }] });
    const final = synth.content.filter(b => b.type === "text").map(b => b.text).join("");
    this.history.push({ role: "assistant", content: final.slice(0, 500) });
    observe("COORDINATOR", "Complete");
    return final;
  }
}

console.log("=".repeat(60));
console.log("M15B — Coordinator (SOLUTION — Node.js)");
console.log("=".repeat(60));

const coord = new Coordinator();
const r1 = await coord.run("Find all UCC filings for Acme Corporation in New York");
console.log(`\nANSWER:\n${r1}`);
const r2 = await coord.run("What's the overall risk level for Acme Corporation?");
console.log(`\nANSWER:\n${r2}`);
const r3 = await coord.run("What about their filings in Texas?");
console.log(`\nANSWER:\n${r3}`);
