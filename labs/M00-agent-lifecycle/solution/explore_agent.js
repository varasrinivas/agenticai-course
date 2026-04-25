/**
 * M00 Lab: UCC Filing Lookup Agent — SOLUTION
 * =============================================
 * Solution — identical to starter for M00 since the lab is explore-only.
 * The agent is already complete. Students run it, read it, and trace its behavior.
 */

import Anthropic from "@anthropic-ai/sdk";
import "dotenv/config";

const client = new Anthropic();

// === COMPONENT 2: Tools ===
const MOCK_FILINGS = {
  "UCC-2024-001": {
    filing_number: "UCC-2024-001",
    filing_date: "2024-01-15",
    debtor: "Greenfield Logistics LLC",
    secured_party: "First National Bank of Commerce",
    collateral: "All inventory, equipment, and accounts receivable",
    status: "Active",
    jurisdiction: "Delaware",
    expiration_date: "2029-01-15",
  },
  "UCC-2024-002": {
    filing_number: "UCC-2024-002",
    filing_date: "2024-03-22",
    debtor: "Greenfield Logistics LLC",
    secured_party: "Pacific Equipment Leasing Corp",
    collateral: "Specific equipment: 12 Class-8 trucks, VINs on file",
    status: "Active",
    jurisdiction: "Delaware",
    expiration_date: "2029-03-22",
  },
  "UCC-2024-003": {
    filing_number: "UCC-2024-003",
    filing_date: "2024-06-10",
    debtor: "Apex Manufacturing Inc",
    secured_party: "Silicon Valley Bank",
    collateral: "All assets including intellectual property and patents",
    status: "Active",
    jurisdiction: "California",
    expiration_date: "2029-06-10",
  },
  "UCC-2023-047": {
    filing_number: "UCC-2023-047",
    filing_date: "2023-09-01",
    debtor: "Coastal Shipping Partners",
    secured_party: "Maritime Finance Group",
    collateral: "Fleet vessels and associated equipment",
    status: "Terminated",
    jurisdiction: "New York",
    expiration_date: "2028-09-01",
  },
  "UCC-2024-005": {
    filing_number: "UCC-2024-005",
    filing_date: "2024-08-18",
    debtor: "Greenfield Logistics LLC",
    secured_party: "Atlas Capital Partners",
    collateral: "Accounts receivable and contract rights",
    status: "Active",
    jurisdiction: "Delaware",
    expiration_date: "2029-08-18",
  },
};

function lookupFiling(filingNumber) {
  const filing = MOCK_FILINGS[filingNumber];
  if (filing) {
    return { found: true, filing };
  }
  return { found: false, error: `No filing found with number ${filingNumber}` };
}

function searchFilings(debtorName) {
  const results = Object.values(MOCK_FILINGS).filter((f) =>
    f.debtor.toLowerCase().includes(debtorName.toLowerCase())
  );
  return {
    query: debtorName,
    count: results.length,
    filings: results,
  };
}

const TOOL_DEFINITIONS = [
  {
    name: "lookup_filing",
    description:
      "Look up a specific UCC filing by its filing number. " +
      "Use this when the user provides a specific filing number like UCC-2024-001.",
    input_schema: {
      type: "object",
      properties: {
        filing_number: {
          type: "string",
          description: "The UCC filing number, e.g. UCC-2024-001",
        },
      },
      required: ["filing_number"],
    },
  },
  {
    name: "search_filings",
    description:
      "Search for UCC filings by debtor name. " +
      "Use this when the user wants to find all filings associated with a company or person. " +
      "Supports partial name matching.",
    input_schema: {
      type: "object",
      properties: {
        debtor_name: {
          type: "string",
          description:
            "The name (or partial name) of the debtor to search for",
        },
      },
      required: ["debtor_name"],
    },
  },
];

const TOOL_FUNCTIONS = {
  lookup_filing: (args) => lookupFiling(args.filing_number),
  search_filings: (args) => searchFilings(args.debtor_name),
};

// === COMPONENT 4: Plan (System Prompt) ===
const SYSTEM_PROMPT = `You are a UCC Filing Research Assistant. Your job is to help users look up and \
understand Uniform Commercial Code (UCC) filings.

You have access to two tools:
- lookup_filing: retrieves a specific filing by its filing number
- search_filings: searches for filings by debtor name

When a user asks about filings, use the appropriate tool to find the data, then \
summarize what you found in clear, plain language. Always mention the filing number, \
debtor, secured party, collateral description, and status.

SCOPE: You ONLY handle UCC filing queries. If the user asks about something unrelated, \
politely explain that you are a specialized UCC filing assistant and cannot help with \
other topics.`;

// === COMPONENT 5: Guardrails ===
const MAX_AGENT_TURNS = 10;
const MAX_QUERY_LENGTH = 500;

function validateQuery(query) {
  if (!query || !query.trim()) {
    return "Query cannot be empty.";
  }
  if (query.length > MAX_QUERY_LENGTH) {
    return `Query too long (${query.length} chars). Maximum is ${MAX_QUERY_LENGTH}.`;
  }
  return null;
}

// === COMPONENT 6: Eyes (Observation) ===
function observe(label, message) {
  console.log(`\n${"=".repeat(60)}`);
  console.log(`[${label}] ${message}`);
  console.log("=".repeat(60));
}

function observeToolCall(toolName, toolInput) {
  console.log(`\n${"─".repeat(60)}`);
  console.log(`[USING TOOL] ${toolName}`);
  console.log(`[INPUT]      ${JSON.stringify(toolInput, null, 2)}`);
  console.log("─".repeat(60));
}

function observeToolResult(result) {
  console.log(`\n${"─".repeat(60)}`);
  console.log("[TOOL RESULT]");
  console.log(JSON.stringify(result, null, 2));
  console.log("─".repeat(60));
}

async function runAgent(userQuery) {
  const error = validateQuery(userQuery);
  if (error) {
    observe("ERROR", error);
    return error;
  }

  observe("QUERY", userQuery);

  const messages = [{ role: "user", content: userQuery }];

  let turn = 0;
  while (turn < MAX_AGENT_TURNS) {
    turn++;
    observe(
      "THINKING",
      `Turn ${turn} — sending ${messages.length} message(s) to Claude...`
    );

    let response;
    try {
      response = await client.messages.create({
        model: "claude-sonnet-4-20250514",
        max_tokens: 1024,
        system: SYSTEM_PROMPT,
        tools: TOOL_DEFINITIONS,
        messages,
      });
    } catch (e) {
      observe("ERROR", `API call failed: ${e.message}`);
      return `Error: API call failed — ${e.message}`;
    }

    if (response.stop_reason === "tool_use") {
      const toolResults = [];
      for (const block of response.content) {
        if (block.type === "tool_use") {
          observeToolCall(block.name, block.input);

          let result;
          if (!(block.name in TOOL_FUNCTIONS)) {
            result = { error: `Unknown tool: ${block.name}` };
          } else {
            try {
              result = TOOL_FUNCTIONS[block.name](block.input);
            } catch (e) {
              result = { error: `Tool execution failed: ${e.message}` };
            }
          }

          observeToolResult(result);
          toolResults.push({
            type: "tool_result",
            tool_use_id: block.id,
            content: JSON.stringify(result),
          });
        }
      }

      messages.push({ role: "assistant", content: response.content });
      messages.push({ role: "user", content: toolResults });
    } else if (response.stop_reason === "end_turn") {
      let finalText = "";
      for (const block of response.content) {
        if (block.text) {
          finalText += block.text;
        }
      }

      observe("RESPONSE", finalText);
      return finalText;
    } else {
      observe("WARNING", `Unexpected stop reason: ${response.stop_reason}`);
      return "Agent stopped unexpectedly.";
    }
  }

  observe("ERROR", `Agent exceeded maximum turns (${MAX_AGENT_TURNS})`);
  return "Error: Agent exceeded maximum number of turns.";
}

// === COMPONENT 7: Home (Deployment) — Entry Point ===
const query =
  process.argv.length > 2
    ? process.argv.slice(2).join(" ")
    : "Find filings for Greenfield Logistics";

console.log("╔══════════════════════════════════════════════════════════╗");
console.log("║        M00 Lab: UCC Filing Lookup Agent                 ║");
console.log("║        Explore the Agent Lifecycle                      ║");
console.log("╚══════════════════════════════════════════════════════════╝");

const result = await runAgent(query);

console.log("\n" + "=".repeat(60));
console.log("FINAL ANSWER:");
console.log("=".repeat(60));
console.log(result);
