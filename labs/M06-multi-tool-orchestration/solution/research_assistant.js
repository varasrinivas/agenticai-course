/**
 * M06 Lab - Step 3: Full Research Assistant with 5 Tools (Solution)
 * ==================================================================
 * Complete solution: a UCC filing research assistant that orchestrates
 * 5 tools to handle complex multi-step research queries.
 *
 * Usage:
 *     node research_assistant.js
 */

import Anthropic from "@anthropic-ai/sdk";
import "dotenv/config";
import { searchFilings, getFilingByNumber } from "../../shared/mock_ucc_data.js";

const client = new Anthropic();
const MODEL = "claude-sonnet-4-20250514";

// =============================================================================
// TOOL IMPLEMENTATIONS
// =============================================================================

function toolSearchFilings({ debtorName, state, status } = {}) {
  const results = searchFilings({ debtorName, state, status });
  const simplified = results.map((f) => ({
    filing_number: f.filing_number,
    debtor: f.debtor.name,
    state: f.state,
    status: f.status,
    type: f.type,
    filing_date: f.filing_date,
  }));
  return { results: simplified, count: simplified.length };
}

function toolGetFilingDetails(filingNumber) {
  const filing = getFilingByNumber(filingNumber);
  if (!filing) {
    return { error: `Filing '${filingNumber}' not found.` };
  }
  return filing;
}

function toolSummarizeText(text) {
  const summaryParts = [];
  const textLower = text.toLowerCase();

  if (textLower.includes("all assets") || textLower.includes("blanket lien")) {
    summaryParts.push(
      "BLANKET LIEN covering essentially all business assets."
    );
  }
  if (textLower.includes("accounts receivable")) {
    summaryParts.push("Covers receivables (money owed to the company).");
  }
  if (textLower.includes("inventory")) {
    summaryParts.push("Covers physical inventory.");
  }
  if (textLower.includes("equipment")) {
    summaryParts.push("Covers equipment and machinery.");
  }
  if (
    textLower.includes("intellectual property") ||
    textLower.includes("patents")
  ) {
    summaryParts.push("Covers intellectual property (patents, trademarks).");
  }
  if (textLower.includes("specific equipment")) {
    summaryParts.push("SPECIFIC EQUIPMENT lien (not blanket).");
  }
  if (textLower.includes("termination")) {
    summaryParts.push("TERMINATION notice -- lien released.");
  }
  if (textLower.includes("general intangibles")) {
    summaryParts.push("Covers intangible assets.");
  }
  if (textLower.includes("farm products") || textLower.includes("crops")) {
    summaryParts.push("Covers farm products and agricultural assets.");
  }
  if (textLower.includes("medical equipment")) {
    summaryParts.push("Covers medical equipment (MRI, CT scanner, etc.).");
  }

  if (summaryParts.length === 0) {
    summaryParts.push("Standard collateral description.");
  }

  return {
    original_length: text.length,
    summary: summaryParts.join(" "),
  };
}

function toolCalculateRiskScore(debtorName, filingCount, collateralTypes) {
  let score = 20;

  const filingFactor = Math.min(filingCount * 15, 45);
  score += filingFactor;

  let collateralFactor = 0;
  for (const ctype of collateralTypes) {
    const ctypeLower = ctype.toLowerCase();
    if (ctypeLower.includes("blanket") || ctypeLower.includes("all assets")) {
      collateralFactor += 20;
    } else if (ctypeLower.includes("specific")) {
      collateralFactor += 5;
    } else if (ctypeLower.includes("intellectual property")) {
      collateralFactor += 15;
    } else if (ctypeLower.includes("termination")) {
      collateralFactor -= 10;
    } else {
      collateralFactor += 10;
    }
  }

  score += Math.min(collateralFactor, 35);
  score = Math.max(0, Math.min(100, score));

  let level;
  if (score >= 75) level = "High";
  else if (score >= 50) level = "Moderate";
  else if (score >= 25) level = "Low";
  else level = "Minimal";

  return {
    debtor_name: debtorName,
    risk_score: score,
    risk_level: level,
    factors: {
      filing_count: filingCount,
      filing_factor: filingFactor,
      collateral_types: collateralTypes,
      collateral_factor: Math.min(collateralFactor, 35),
    },
  };
}

function toolGenerateReport(title, filings, summary = null) {
  const lines = [];
  lines.push("=".repeat(50));
  lines.push(`  UCC FILING REPORT: ${title}`);
  lines.push("=".repeat(50));
  lines.push(`Total Filings: ${filings.length}`);
  lines.push("");

  filings.forEach((filing, i) => {
    lines.push(`--- Filing ${i + 1} ---`);
    if (typeof filing === "object" && filing !== null) {
      for (const [key, value] of Object.entries(filing)) {
        if (typeof value === "object" && value !== null) {
          lines.push(`  ${key}:`);
          for (const [k, v] of Object.entries(value)) {
            lines.push(`    ${k}: ${v}`);
          }
        } else {
          lines.push(`  ${key}: ${value}`);
        }
      }
    }
    lines.push("");
  });

  if (summary) {
    lines.push("--- Summary ---");
    lines.push(summary);
    lines.push("");
  }

  lines.push("=".repeat(50));
  lines.push("  END OF REPORT");
  lines.push("=".repeat(50));

  const reportText = lines.join("\n");
  return {
    report: reportText,
    filing_count: filings.length,
    report_length: reportText.length,
  };
}

// =============================================================================
// TOOL DEFINITIONS
// =============================================================================

const TOOLS = [
  {
    name: "search_filings",
    description:
      "Search UCC filings by debtor name, state, and/or status. " +
      "Returns a simplified list of matching filings with filing number, " +
      "debtor name, state, status, type, and filing date.",
    input_schema: {
      type: "object",
      properties: {
        debtor_name: {
          type: "string",
          description: "Partial or full debtor name to search for",
        },
        state: {
          type: "string",
          description: "State to filter by, e.g. 'New York', 'Texas'",
        },
        status: {
          type: "string",
          description:
            "Filing status: 'Active', 'Terminated', 'Lapsed', 'Amendment'",
        },
      },
    },
  },
  {
    name: "get_filing_details",
    description:
      "Get full details for a specific UCC filing by its filing number. " +
      "Returns complete information including debtor address, secured party, " +
      "collateral description, filing dates, and document numbers.",
    input_schema: {
      type: "object",
      properties: {
        filing_number: {
          type: "string",
          description:
            "The UCC filing number, e.g. 'UCC-2024-NY-0012847'",
        },
      },
      required: ["filing_number"],
    },
  },
  {
    name: "summarize_text",
    description:
      "Summarize a collateral description into plain English. " +
      "Identifies the type of lien (blanket vs specific), key asset categories, " +
      "and any special conditions (termination, amendment, etc.).",
    input_schema: {
      type: "object",
      properties: {
        text: {
          type: "string",
          description: "The collateral description text to summarize",
        },
      },
      required: ["text"],
    },
  },
  {
    name: "calculate_risk_score",
    description:
      "Calculate a lien risk score (0-100) for a debtor based on their " +
      "filing count and collateral types. Returns score, risk level " +
      "(Minimal/Low/Moderate/High), and contributing factors.",
    input_schema: {
      type: "object",
      properties: {
        debtor_name: {
          type: "string",
          description: "The debtor's name",
        },
        filing_count: {
          type: "integer",
          description: "Number of active filings for this debtor",
        },
        collateral_types: {
          type: "array",
          items: { type: "string" },
          description:
            "List of collateral type descriptions, e.g. " +
            "['blanket lien', 'specific equipment']",
        },
      },
      required: ["debtor_name", "filing_count", "collateral_types"],
    },
  },
  {
    name: "generate_report",
    description:
      "Generate a formatted text report from filing data. " +
      "Takes a title, list of filing objects, and optional summary text.",
    input_schema: {
      type: "object",
      properties: {
        title: {
          type: "string",
          description: "Report title, e.g. 'Filings in Texas'",
        },
        filings: {
          type: "array",
          items: { type: "object" },
          description: "List of filing objects to include in the report",
        },
        summary: {
          type: "string",
          description:
            "Optional summary text to include at the end of the report",
        },
      },
      required: ["title", "filings"],
    },
  },
];

// =============================================================================
// TOOL DISPATCHER
// =============================================================================

const TOOL_FUNCTIONS = {
  search_filings: (args) =>
    toolSearchFilings({
      debtorName: args.debtor_name,
      state: args.state,
      status: args.status,
    }),
  get_filing_details: (args) => toolGetFilingDetails(args.filing_number),
  summarize_text: (args) => toolSummarizeText(args.text),
  calculate_risk_score: (args) =>
    toolCalculateRiskScore(
      args.debtor_name,
      args.filing_count,
      args.collateral_types
    ),
  generate_report: (args) =>
    toolGenerateReport(args.title, args.filings, args.summary),
};

const MAX_TURNS = 15;

const SYSTEM_PROMPT = `You are a UCC filing research assistant with access to 5 tools:

1. search_filings: Search for UCC filings by debtor name, state, or status
2. get_filing_details: Get complete details for a specific filing number
3. summarize_text: Summarize collateral descriptions into plain English
4. calculate_risk_score: Calculate lien risk score based on filing count and collateral types
5. generate_report: Generate a formatted report from filing data

RESEARCH WORKFLOW:
- Start by searching for relevant filings
- Get details for specific filings when needed
- Summarize collateral in plain English when asked
- Calculate risk scores when evaluating a debtor's lien exposure
- Generate reports when asked for formatted output

Always explain your findings clearly. When you use multiple tools, explain
how the information from each step connects to your final answer.`;

// =============================================================================
// OBSERVATION HELPERS
// =============================================================================

function observe(label, message) {
  console.log(`\n${"=".repeat(60)}`);
  console.log(`[${label}] ${message}`);
  console.log("=".repeat(60));
}

function observeToolCall(toolName, toolInput) {
  let inputStr = JSON.stringify(toolInput, null, 2);
  if (inputStr.length > 300) {
    inputStr = inputStr.substring(0, 300) + "\n  ... (truncated)";
  }
  console.log(`\n${"─".repeat(60)}`);
  console.log(`[USING TOOL] ${toolName}`);
  console.log(`[INPUT]      ${inputStr}`);
  console.log("─".repeat(60));
}

function observeToolResult(toolName, result) {
  let resultStr = JSON.stringify(result, null, 2);
  if (resultStr.length > 500) {
    resultStr = resultStr.substring(0, 500) + "\n  ... (truncated)";
  }
  console.log(`\n${"─".repeat(60)}`);
  console.log(`[TOOL RESULT] ${toolName}`);
  console.log(resultStr);
  console.log("─".repeat(60));
}

// =============================================================================
// SOLUTION: The 5-Tool Agent Loop
// =============================================================================

async function runAgent(userMessage) {
  /**
   * Run the research assistant agent with 5 tools.
   *
   * WHY 5 tools matters: With more tools available, Claude must make smarter
   * selection decisions. The agent loop is the same pattern -- what changes
   * is the complexity of tool orchestration. Claude may:
   * - Call a single tool (simple lookup)
   * - Chain 2-3 tools sequentially (search -> details -> summarize)
   * - Use parallel calls (search multiple states at once)
   * - Mix parallel and sequential in one conversation
   */
  observe("QUERY", userMessage);

  // Initialize conversation memory
  const messages = [{ role: "user", content: userMessage }];
  let totalToolCalls = 0;
  const toolsUsed = []; // Track all tools used

  // === THE AGENT LOOP ===
  let turn = 0;
  while (turn < MAX_TURNS) {
    turn++;
    observe(
      "THINKING",
      `Turn ${turn} -- sending ${messages.length} message(s) to Claude...`
    );

    // DECIDE: Ask Claude what to do next
    const response = await client.messages.create({
      model: MODEL,
      max_tokens: 4096, // Larger for reports
      system: SYSTEM_PROMPT,
      tools: TOOLS,
      messages,
    });

    if (response.stop_reason === "tool_use") {
      // ACT: Execute all tool calls from this turn
      const toolResults = [];

      for (const block of response.content) {
        if (block.type === "tool_use") {
          observeToolCall(block.name, block.input);

          // Dispatch to the correct tool function
          let result;
          if (block.name in TOOL_FUNCTIONS) {
            try {
              result = TOOL_FUNCTIONS[block.name](block.input);
            } catch (e) {
              // Catch tool execution errors and report them back
              // WHY: Claude can recover from errors if we tell it what happened
              result = {
                error: `Tool '${block.name}' failed: ${e.message}`,
              };
            }
          } else {
            // Unknown tool -- should never happen with correct definitions
            result = { error: `Unknown tool: ${block.name}` };
          }

          observeToolResult(block.name, result);

          toolResults.push({
            type: "tool_result",
            tool_use_id: block.id,
            content: JSON.stringify(result),
          });

          // Track usage
          toolsUsed.push(block.name);
          totalToolCalls++;
        }
      }

      // OBSERVE: Add to conversation memory
      messages.push({ role: "assistant", content: response.content });
      messages.push({ role: "user", content: toolResults });
    } else if (response.stop_reason === "end_turn") {
      // Claude is done -- extract text
      let finalText = "";
      for (const block of response.content) {
        if (block.text) {
          finalText += block.text;
        }
      }

      // Print usage summary
      const unique = [...new Set(toolsUsed)].sort();
      console.log(
        `\n[SUMMARY] ${totalToolCalls} tool calls using ` +
          `${unique.length} unique tools: ${unique.join(", ")}`
      );

      observe("RESPONSE", finalText);
      return finalText;
    } else {
      observe("WARNING", `Unexpected stop reason: ${response.stop_reason}`);
      return "Agent stopped unexpectedly.";
    }
  }

  observe("ERROR", `Agent exceeded maximum turns (${MAX_TURNS})`);
  return "Error: Agent exceeded maximum number of turns.";
}

// =============================================================================
// MAIN
// =============================================================================

console.log("=".repeat(60));
console.log("M06 Lab - Step 3: Full Research Assistant (5 Tools) (SOLUTION)");
console.log("=".repeat(60));

// Test 1: Search + summarize
console.log("\n\n>>> Test 1: Search + summarize");
const result1 = await runAgent(
  "Find all active filings in New York and summarize their collateral"
);
console.log(`\nFINAL ANSWER: ${result1}`);

// Test 2: Search + risk score
console.log("\n\n>>> Test 2: Search + risk score");
const result2 = await runAgent(
  "What's the risk score for Greenfield Logistics LLC?"
);
console.log(`\nFINAL ANSWER: ${result2}`);

// Test 3: Search + details + report
console.log("\n\n>>> Test 3: Search + details + report");
const result3 = await runAgent("Generate a report on all filings in Texas");
console.log(`\nFINAL ANSWER: ${result3}`);
