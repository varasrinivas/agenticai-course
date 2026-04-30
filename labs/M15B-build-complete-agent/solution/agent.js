/**
 * M15B — Single ReAct Agent (Solution — Node.js)
 * =================================================
 *
 * Usage:
 *     node agent.js
 */

import Anthropic from "@anthropic-ai/sdk";
import { config } from "dotenv";

config();

const client = new Anthropic();
const MODEL = "claude-sonnet-4-6";

// =============================================================================
// MOCK DATA (inline — same 15 filings as mock_data.py)
// =============================================================================

const MOCK_FILINGS = [
  { filing_number: "UCC-2024-NY-0012847", type: "UCC-1", state: "New York", filing_date: "2024-03-15", expiration_date: "2029-03-15", status: "Active", debtor: { name: "Acme Corporation" }, secured_party: { name: "Atlantic Capital Partners" }, collateral_description: "All accounts receivable, inventory, equipment, and general intangibles now owned or hereafter acquired by Debtor." },
  { filing_number: "UCC-2024-NY-0015921", type: "UCC-1", state: "New York", filing_date: "2024-05-22", expiration_date: "2029-05-22", status: "Active", debtor: { name: "Acme Corporation" }, secured_party: { name: "Citibank N.A." }, collateral_description: "All deposit accounts, investment property, and letter-of-credit rights held at or through Citibank." },
  { filing_number: "UCC-2023-NY-0145678", type: "UCC-3", state: "New York", filing_date: "2023-12-01", expiration_date: null, status: "Terminated", debtor: { name: "Harbor Shipping International Inc" }, secured_party: { name: "Citibank N.A." }, collateral_description: "TERMINATION." },
  { filing_number: "UCC-2024-NY-0019004", type: "UCC-1", state: "New York", filing_date: "2024-08-10", expiration_date: "2029-08-10", status: "Active", debtor: { name: "Greenfield Logistics LLC" }, secured_party: { name: "JPMorgan Chase Bank N.A." }, collateral_description: "All inventory held at debtor's warehouse facilities in New York State; all accounts receivable." },
  { filing_number: "UCC-2024-CA-0098231", type: "UCC-1", state: "California", filing_date: "2024-01-22", expiration_date: "2029-01-22", status: "Active", debtor: { name: "Pacific Ridge Technologies Inc" }, secured_party: { name: "Silicon Valley Bank" }, collateral_description: "All assets of the Debtor including intellectual property, patents, trademarks, accounts, deposit accounts, investment property." },
  { filing_number: "UCC-2024-CA-0101457", type: "UCC-1", state: "California", filing_date: "2024-04-03", expiration_date: "2029-04-03", status: "Active", debtor: { name: "Acme Corporation" }, secured_party: { name: "Bank of America N.A." }, collateral_description: "All equipment and fixtures located at debtor's San Francisco and Los Angeles offices." },
  { filing_number: "UCC-2023-CA-0087652", type: "UCC-3", state: "California", filing_date: "2023-11-15", expiration_date: "2028-06-30", status: "Amendment", debtor: { name: "Pacific Ridge Technologies Inc" }, secured_party: { name: "Silicon Valley Bank" }, collateral_description: "Amendment to add: all software source code repositories, SaaS subscription contracts." },
  { filing_number: "UCC-2023-TX-0187634", type: "UCC-1", state: "Texas", filing_date: "2023-09-10", expiration_date: "2028-09-10", status: "Active", debtor: { name: "Lone Star Energy Solutions LP" }, secured_party: { name: "Wells Fargo Equipment Finance" }, collateral_description: "Specific equipment: (3) Caterpillar 349F L hydraulic excavators; (1) Liebherr LTM 1300-6.2 mobile crane." },
  { filing_number: "UCC-2024-TX-0201337", type: "UCC-1", state: "Texas", filing_date: "2024-02-28", expiration_date: "2029-02-28", status: "Active", debtor: { name: "Acme Corporation" }, secured_party: { name: "PNC Bank N.A." }, collateral_description: "All accounts receivable and contract rights arising from debtor's Texas operations." },
  { filing_number: "UCC-2024-TX-0215890", type: "UCC-1", state: "Texas", filing_date: "2024-06-15", expiration_date: "2029-06-15", status: "Active", debtor: { name: "Lone Star Energy Solutions LP" }, secured_party: { name: "Caterpillar Financial Services Corp" }, collateral_description: "Specific equipment: (2) Caterpillar D10T2 track-type tractors." },
  { filing_number: "UCC-2024-FL-0054219", type: "UCC-3", state: "Florida", filing_date: "2024-06-01", expiration_date: "2027-11-18", status: "Amendment", debtor: { name: "Sunshine Medical Group PA" }, secured_party: { name: "TD Bank N.A." }, collateral_description: "Amendment to add: (2) Siemens MRI systems and (1) GE Revolution CT scanner." },
  { filing_number: "UCC-2024-FL-0059811", type: "UCC-1", state: "Florida", filing_date: "2024-07-20", expiration_date: "2029-07-20", status: "Active", debtor: { name: "Acme Corporation" }, secured_party: { name: "Atlantic Capital Partners" }, collateral_description: "All accounts receivable, inventory, and general intangibles of debtor's Florida division." },
  { filing_number: "UCC-2024-IL-0076543", type: "UCC-1", state: "Illinois", filing_date: "2024-02-14", expiration_date: "2029-02-14", status: "Active", debtor: { name: "Midwest Agricultural Cooperative" }, secured_party: { name: "Farm Credit Services of America" }, collateral_description: "All farm products, crops, livestock, and farm equipment. All accounts and proceeds." },
  { filing_number: "UCC-2024-IL-0081290", type: "UCC-1", state: "Illinois", filing_date: "2024-04-30", expiration_date: "2029-04-30", status: "Active", debtor: { name: "Acme Corporation" }, secured_party: { name: "JPMorgan Chase Bank N.A." }, collateral_description: "All assets of debtor's Illinois subsidiary including accounts, inventory, equipment." },
  { filing_number: "UCC-2023-IL-0069221", type: "UCC-3", state: "Illinois", filing_date: "2023-10-05", expiration_date: "2028-02-14", status: "Amendment", debtor: { name: "Midwest Agricultural Cooperative" }, secured_party: { name: "Farm Credit Services of America" }, collateral_description: "Amendment to add: grain storage equipment and (4) John Deere S790 combines." },
];

function searchFilings({ debtorName, state } = {}) {
  let results = MOCK_FILINGS;
  if (debtorName) results = results.filter(f => f.debtor.name.toLowerCase().includes(debtorName.toLowerCase()));
  if (state) results = results.filter(f => f.state.toLowerCase() === state.toLowerCase());
  return results;
}

function getFilingByNumber(num) { return MOCK_FILINGS.find(f => f.filing_number === num) || null; }

function calculateRisk(name) {
  const filings = searchFilings({ debtorName: name });
  if (!filings.length) return { debtor: name, risk_score: 0, risk_level: "UNKNOWN", message: "No filings found" };
  const active = filings.filter(f => f.status === "Active");
  const blanket = filings.filter(f => f.collateral_description.toLowerCase().includes("all assets") || f.collateral_description.toLowerCase().includes("all accounts"));
  const amend = filings.filter(f => f.type === "UCC-3");
  const states = [...new Set(filings.map(f => f.state))];
  const parties = [...new Set(filings.map(f => f.secured_party.name))];
  let score = Math.min(1.0, active.length * 0.15 + blanket.length * 0.2 + amend.length * 0.05 + (states.length > 1 ? 0.1 : 0) + (parties.length > 1 ? 0.1 : 0));
  score = Math.round(score * 100) / 100;
  const level = score >= 0.7 ? "HIGH" : score >= 0.4 ? "MEDIUM" : "LOW";
  return { debtor: name, risk_score: score, risk_level: level, total_filings: filings.length, active_filings: active.length, blanket_liens: blanket.length, amendments: amend.length, states: states.sort(), secured_parties: parties.sort(),
    factors: [`${active.length} active filings`, `${blanket.length} blanket liens`, `${amend.length} amendments`, `${states.length} states`, `${parties.length} secured parties`] };
}

const TOOLS = [
  { name: "search_filings", description: "Search UCC filings by debtor name and/or state.", input_schema: { type: "object", properties: { debtor_name: { type: "string" }, state: { type: "string" } }, required: [] } },
  { name: "get_filing_details", description: "Get full filing details.", input_schema: { type: "object", properties: { filing_number: { type: "string" } }, required: ["filing_number"] } },
  { name: "calculate_risk_score", description: "Calculate risk profile for a debtor.", input_schema: { type: "object", properties: { debtor_name: { type: "string" } }, required: ["debtor_name"] } },
];

function executeTool(name, input) {
  try {
    if (name === "search_filings") {
      const r = searchFilings({ debtorName: input.debtor_name, state: input.state });
      if (!r.length) return JSON.stringify({ message: "No filings found" });
      return JSON.stringify(r.map(f => ({ filing_number: f.filing_number, debtor: f.debtor.name, secured_party: f.secured_party.name, state: f.state, status: f.status, type: f.type, collateral: f.collateral_description.slice(0,120)+"..." })), null, 2);
    } else if (name === "get_filing_details") {
      const f = getFilingByNumber(input.filing_number);
      return f ? JSON.stringify(f, null, 2) : JSON.stringify({ error: "Not found" });
    } else if (name === "calculate_risk_score") { return JSON.stringify(calculateRisk(input.debtor_name), null, 2); }
    return JSON.stringify({ error: `Unknown: ${name}` });
  } catch (e) { return JSON.stringify({ error: e.message }); }
}

function observe(label, msg) { console.log(`\n${"=".repeat(60)}\n[${label}] ${msg}\n${"=".repeat(60)}`); }

const SYSTEM = `You are a UCC filing research agent. Use tools to find information. Never guess. Cite filing numbers.
Tools: search_filings, get_filing_details, calculate_risk_score.`;

async function runAgent(query, maxTurns = 10) {
  observe("QUERY", query);
  const messages = [{ role: "user", content: query }];
  for (let t = 0; t < maxTurns; t++) {
    const resp = await client.messages.create({ model: MODEL, max_tokens: 4096, system: SYSTEM, tools: TOOLS, messages });
    if (resp.stop_reason !== "tool_use") {
      const text = resp.content.filter(b => b.type === "text").map(b => b.text).join("");
      observe("RESPONSE", text.slice(0, 200));
      return text;
    }
    const results = [];
    for (const b of resp.content) { if (b.type === "tool_use") results.push({ type: "tool_result", tool_use_id: b.id, content: executeTool(b.name, b.input) }); }
    messages.push({ role: "assistant", content: resp.content });
    messages.push({ role: "user", content: results });
  }
  return "Agent did not complete.";
}

console.log("=".repeat(60));
console.log("M15B — Single Agent (SOLUTION — Node.js)");
console.log("=".repeat(60));

const r1 = await runAgent("Find all UCC filings for Acme Corporation in New York");
console.log(`\nANSWER:\n${r1}`);

const r2 = await runAgent("What's the risk level for Acme Corporation?");
console.log(`\nANSWER:\n${r2}`);
