/**
 * M12 Lab — The ReAct Agent Loop (Solution)
 * ==========================================
 * Complete ReAct agent with full trace logging.
 *
 * Usage:
 *     node react_agent.js
 */

import Anthropic from "@anthropic-ai/sdk";
import { config } from "dotenv";
import { dirname, join } from "path";
import { fileURLToPath, pathToFileURL } from "url";

config();

const __dirname = dirname(fileURLToPath(import.meta.url));
const mockDataPath = join(__dirname, "..", "..", "shared", "mock_ucc_data.js");
// pathToFileURL: ESM import() needs a file:// URL, not a filesystem path.
// A bare Windows path (D:\...) is read as protocol 'd:' and rejected with
// ERR_UNSUPPORTED_ESM_URL_SCHEME. Posix paths happen to work, which is why
// this only breaks on Windows.
const { searchFilings, getFilingByNumber } = await import(pathToFileURL(mockDataPath).href);

const client = new Anthropic();
const MODEL = "claude-sonnet-4-6";

// =============================================================================
// OBSERVATION HELPERS
// =============================================================================

function observe(label, message) {
  console.log(`\n${"=".repeat(60)}`);
  console.log(`[${label}] ${message}`);
  console.log("=".repeat(60));
}

function observeToolCall(toolName, toolInput) {
  console.log(`\n${"─".repeat(60)}`);
  console.log(`[ACT]   Tool: ${toolName}`);
  console.log(`[INPUT] ${JSON.stringify(toolInput, null, 2)}`);
  console.log("─".repeat(60));
}

function observeToolResult(result) {
  console.log(`\n${"─".repeat(60)}`);
  console.log("[OBSERVE] Tool result:");
  const text = typeof result === "string" ? result : JSON.stringify(result, null, 2);
  console.log(text.length > 500 ? text.slice(0, 500) + "\n... (truncated)" : text);
  console.log("─".repeat(60));
}

function observeThinking(text) {
  console.log(`\n${"─".repeat(60)}`);
  console.log(`[THINK] ${text.slice(0, 300)}${text.length > 300 ? "..." : ""}`);
  console.log("─".repeat(60));
}

// =============================================================================
// TOOLS
// =============================================================================

const TOOLS = [
  {
    name: "search_filings",
    description: "Search UCC filings by debtor name and/or state.",
    input_schema: {
      type: "object",
      properties: {
        debtor_name: { type: "string", description: "Full or partial debtor name" },
        state: { type: "string", description: "US state to filter results" },
      },
      required: [],
    },
  },
  {
    name: "get_filing_details",
    description: "Get the full details of a specific UCC filing by its filing number.",
    input_schema: {
      type: "object",
      properties: { filing_number: { type: "string", description: "The UCC filing number" } },
      required: ["filing_number"],
    },
  },
  {
    name: "calculate_risk",
    description: "Calculate a risk profile for a debtor based on their UCC filings.",
    input_schema: {
      type: "object",
      properties: { debtor_name: { type: "string", description: "The debtor name to assess" } },
      required: ["debtor_name"],
    },
  },
];

function calculateRiskForDebtor(debtorName) {
  const filings = searchFilings({ debtorName });
  if (filings.length === 0) {
    return { debtor: debtorName, risk_score: 0, risk_level: "UNKNOWN", message: `No filings found for '${debtorName}'` };
  }
  const active = filings.filter((f) => f.status === "Active");
  const blanket = filings.filter((f) => f.collateral_description.toLowerCase().includes("all assets") || f.collateral_description.toLowerCase().includes("all accounts"));
  const amendments = filings.filter((f) => f.type === "UCC-3");
  const score = Math.min(1.0, active.length * 0.25 + blanket.length * 0.3 + amendments.length * 0.1);
  let level, rec;
  if (score >= 0.7) { level = "HIGH"; rec = "Significant lien exposure. Detailed due diligence recommended."; }
  else if (score >= 0.4) { level = "MEDIUM"; rec = "Moderate lien activity. Review collateral descriptions."; }
  else { level = "LOW"; rec = "Limited lien exposure. Standard credit procedures should suffice."; }
  return {
    debtor: debtorName, risk_score: Math.round(score * 100) / 100, risk_level: level,
    total_filings: filings.length, active_filings: active.length, blanket_liens: blanket.length,
    amendments: amendments.length, recommendation: rec,
    factors: [`${active.length} active filing(s)`, `${blanket.length} blanket lien(s)`, `${amendments.length} amendment(s)`],
  };
}

function executeTool(toolName, toolInput) {
  try {
    if (toolName === "search_filings") {
      const results = searchFilings({ debtorName: toolInput.debtor_name, state: toolInput.state });
      return JSON.stringify(results.map((f) => ({
        filing_number: f.filing_number, debtor: f.debtor.name, secured_party: f.secured_party.name,
        state: f.state, status: f.status, type: f.type,
        collateral: f.collateral_description.slice(0, 120) + "...",
      })), null, 2);
    } else if (toolName === "get_filing_details") {
      const filing = getFilingByNumber(toolInput.filing_number);
      return filing ? JSON.stringify(filing, null, 2) : JSON.stringify({ error: `Filing not found` });
    } else if (toolName === "calculate_risk") {
      return JSON.stringify(calculateRiskForDebtor(toolInput.debtor_name), null, 2);
    }
    return JSON.stringify({ error: `Unknown tool: ${toolName}` });
  } catch (e) {
    return JSON.stringify({ error: `Tool execution failed: ${e.message}` });
  }
}

const SYSTEM_PROMPT = `You are a UCC filing research agent. Use tools to find information. Never guess. Cite filing numbers.

Tools: search_filings, get_filing_details, calculate_risk.
- Search first, then get details or calculate risk as needed.
- If no results, say so clearly.`;

// =============================================================================
// REACT AGENT LOOP — SOLUTION
// =============================================================================

async function runReactAgent(userQuery, maxTurns = 10) {
  observe("QUERY", userQuery);

  const messages = [{ role: "user", content: userQuery }];

  for (let turn = 0; turn < maxTurns; turn++) {
    const response = await client.messages.create({
      model: MODEL,
      max_tokens: 4096,
      system: SYSTEM_PROMPT,
      tools: TOOLS,
      messages,
    });

    // STOP CONDITION: Claude has a final answer
    if (response.stop_reason !== "tool_use") {
      let finalText = "";
      for (const block of response.content) {
        if (block.type === "text") finalText += block.text;
      }
      observe("RESPONSE", finalText.slice(0, 200) + (finalText.length > 200 ? "..." : ""));
      return finalText;
    }

    // CONTINUE: Process tool calls
    const toolResults = [];
    for (const block of response.content) {
      if (block.type === "tool_use") {
        observeToolCall(block.name, block.input);
        const result = executeTool(block.name, block.input);
        observeToolResult(result);
        toolResults.push({ type: "tool_result", tool_use_id: block.id, content: result });
      } else if (block.type === "text") {
        observeThinking(block.text);
      }
    }

    messages.push({ role: "assistant", content: response.content });
    messages.push({ role: "user", content: toolResults });
  }

  return "Agent did not produce a final response within max turns.";
}

// =============================================================================
// MAIN
// =============================================================================

console.log("=".repeat(60));
console.log("M12 Lab — The ReAct Agent Loop (SOLUTION)");
console.log("=".repeat(60));

console.log("\n\n>>> Query 1: Find filings for Greenfield Logistics");
const r1 = await runReactAgent("Find all UCC filings for Greenfield Logistics in New York");
console.log(`\nFINAL ANSWER:\n${r1}`);

console.log("\n\n>>> Query 2: Risk profile for Nextera Holdings");
const r2 = await runReactAgent("What's the risk profile for Nextera Holdings Corp?");
console.log(`\nFINAL ANSWER:\n${r2}`);

console.log("\n\n>>> Query 3: Texas filings and collateral");
const r3 = await runReactAgent("Search for filings in Texas and tell me about the collateral");
console.log(`\nFINAL ANSWER:\n${r3}`);
