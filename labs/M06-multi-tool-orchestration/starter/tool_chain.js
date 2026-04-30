/**
 * M06 Lab - Step 2: Sequential Tool Chain (Starter)
 * ===================================================
 * Build an agent loop that supports multi-turn tool chaining:
 * the output of one tool feeds into Claude's decision to call the next.
 *
 * Claude drives the chain -- you don't hardcode the order.
 *
 * Usage:
 *     node tool_chain.js
 */

import Anthropic from "@anthropic-ai/sdk";
import "dotenv/config";

const client = new Anthropic();
const MODEL = "claude-sonnet-4-6";

// =============================================================================
// INLINE MOCK DATA (complete -- do not modify)
// =============================================================================

const MOCK_FILINGS_DB = [
  {
    filing_number: "UCC-2024-001",
    debtor: "Greenfield Logistics LLC",
    state: "New York",
    status: "Active",
    collateral_summary:
      "All accounts receivable, inventory, equipment, and general intangibles now owned or hereafter acquired by Debtor.",
  },
  {
    filing_number: "UCC-2024-002",
    debtor: "Pacific Ridge Technologies Inc",
    state: "California",
    status: "Active",
    collateral_summary:
      "All assets of the Debtor including but not limited to: intellectual property, patents, trademarks, accounts, deposit accounts, investment property, and all proceeds thereof.",
  },
  {
    filing_number: "UCC-2023-003",
    debtor: "Lone Star Energy Solutions LP",
    state: "Texas",
    status: "Active",
    collateral_summary:
      "Specific equipment: (3) Caterpillar 349F L hydraulic excavators, serial numbers CAT349F-8821, CAT349F-8822, CAT349F-8823; (1) Liebherr LTM 1300-6.2 mobile crane, serial number LTM-DE-90124.",
  },
  {
    filing_number: "UCC-2024-004",
    debtor: "Harbor Shipping International Inc",
    state: "New York",
    status: "Terminated",
    collateral_summary:
      "TERMINATION -- This filing terminates the effectiveness of the original filing.",
  },
];

const MOCK_FILING_DETAILS = {
  "UCC-2024-001": {
    filing_number: "UCC-2024-001",
    type: "UCC-1",
    debtor: "Greenfield Logistics LLC",
    debtor_address: "450 West 33rd Street, Suite 800, New York, NY 10001",
    secured_party: "Atlantic Capital Partners",
    state: "New York",
    filing_date: "2024-03-15",
    expiration_date: "2029-03-15",
    status: "Active",
    collateral_description:
      "All accounts receivable, inventory, equipment, and general intangibles now owned or hereafter acquired by Debtor. This is a blanket lien covering all present and future assets used in the ordinary course of business.",
  },
  "UCC-2024-002": {
    filing_number: "UCC-2024-002",
    type: "UCC-1",
    debtor: "Pacific Ridge Technologies Inc",
    debtor_address: "2800 Sand Hill Road, Menlo Park, CA 94025",
    secured_party: "Silicon Valley Bank",
    state: "California",
    filing_date: "2024-01-22",
    expiration_date: "2029-01-22",
    status: "Active",
    collateral_description:
      "All assets of the Debtor including but not limited to: intellectual property, patents, trademarks, accounts, deposit accounts, investment property, and all proceeds thereof. This filing represents a comprehensive security interest in all tangible and intangible assets.",
  },
  "UCC-2023-003": {
    filing_number: "UCC-2023-003",
    type: "UCC-1",
    debtor: "Lone Star Energy Solutions LP",
    debtor_address: "1200 Smith Street, Suite 3000, Houston, TX 77002",
    secured_party: "Wells Fargo Equipment Finance",
    state: "Texas",
    filing_date: "2023-09-10",
    expiration_date: "2028-09-10",
    status: "Active",
    collateral_description:
      "Specific equipment: (3) Caterpillar 349F L hydraulic excavators, serial numbers CAT349F-8821, CAT349F-8822, CAT349F-8823; (1) Liebherr LTM 1300-6.2 mobile crane, serial number LTM-DE-90124. This is a purchase money security interest (PMSI) in specific identified equipment.",
  },
  "UCC-2024-004": {
    filing_number: "UCC-2024-004",
    type: "UCC-3",
    debtor: "Harbor Shipping International Inc",
    debtor_address: "One World Trade Center, Floor 72, New York, NY 10007",
    secured_party: "Citibank N.A.",
    state: "New York",
    filing_date: "2023-12-01",
    expiration_date: null,
    status: "Terminated",
    collateral_description:
      "TERMINATION -- This filing terminates the effectiveness of the original filing UCC-2019-NY-0089012. All collateral previously encumbered is now released.",
  },
};

// =============================================================================
// TOOL FUNCTIONS (complete -- do not modify)
// =============================================================================

function searchFilings({ debtorName, state, status } = {}) {
  let results = MOCK_FILINGS_DB;
  if (debtorName)
    results = results.filter((f) =>
      f.debtor.toLowerCase().includes(debtorName.toLowerCase())
    );
  if (state)
    results = results.filter(
      (f) => f.state.toLowerCase() === state.toLowerCase()
    );
  if (status)
    results = results.filter(
      (f) => f.status.toLowerCase() === status.toLowerCase()
    );

  if (results.length === 0) {
    return {
      results: [],
      count: 0,
      message: "No filings found matching your criteria.",
    };
  }
  return { results, count: results.length };
}

function getFilingDetails(filingNumber) {
  if (filingNumber in MOCK_FILING_DETAILS) {
    return MOCK_FILING_DETAILS[filingNumber];
  }
  return {
    error: `Filing '${filingNumber}' not found. Available: ${Object.keys(MOCK_FILING_DETAILS).join(", ")}`,
  };
}

function summarizeText(text) {
  const summaryParts = [];
  const textLower = text.toLowerCase();

  if (textLower.includes("all assets") || textLower.includes("blanket lien")) {
    summaryParts.push(
      "This is a BLANKET LIEN covering essentially all business assets."
    );
  }
  if (textLower.includes("accounts receivable")) {
    summaryParts.push("Covers money owed to the company (receivables).");
  }
  if (textLower.includes("inventory")) {
    summaryParts.push("Covers physical inventory and stock.");
  }
  if (textLower.includes("equipment")) {
    summaryParts.push("Covers business equipment and machinery.");
  }
  if (
    textLower.includes("intellectual property") ||
    textLower.includes("patents")
  ) {
    summaryParts.push(
      "Covers intellectual property (patents, trademarks, etc.)."
    );
  }
  if (textLower.includes("specific equipment")) {
    summaryParts.push(
      "Covers SPECIFIC identified equipment (not a blanket lien)."
    );
  }
  if (textLower.includes("termination")) {
    summaryParts.push(
      "This is a TERMINATION notice -- the original lien has been released."
    );
  }
  if (textLower.includes("general intangibles")) {
    summaryParts.push("Covers intangible assets (contracts, goodwill, etc.).");
  }

  if (summaryParts.length === 0) {
    summaryParts.push(
      "Standard collateral description -- review full text for details."
    );
  }

  return {
    original_length: text.length,
    summary: summaryParts.join(" "),
  };
}

// =============================================================================
// TOOL DEFINITIONS (complete -- do not modify)
// =============================================================================

const TOOLS = [
  {
    name: "search_filings",
    description:
      "Search UCC filings by debtor name, state, and/or status. " +
      "Returns a list of matching filings with basic info.",
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
          description: "Filing status: 'Active', 'Terminated', 'Lapsed'",
        },
      },
    },
  },
  {
    name: "get_filing_details",
    description:
      "Get full details for a specific UCC filing by its filing number. " +
      "Returns debtor info, secured party, collateral description, dates, etc.",
    input_schema: {
      type: "object",
      properties: {
        filing_number: {
          type: "string",
          description: "The UCC filing number, e.g. 'UCC-2024-001'",
        },
      },
      required: ["filing_number"],
    },
  },
  {
    name: "summarize_text",
    description:
      "Summarize a collateral description into plain English. " +
      "Identifies the type of lien (blanket vs specific) and key asset categories.",
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
];

// Dispatch map: tool name -> function that executes it
const TOOL_FUNCTIONS = {
  search_filings: (args) =>
    searchFilings({
      debtorName: args.debtor_name,
      state: args.state,
      status: args.status,
    }),
  get_filing_details: (args) => getFilingDetails(args.filing_number),
  summarize_text: (args) => summarizeText(args.text),
};

const MAX_TURNS = 10;

const SYSTEM_PROMPT = `You are a UCC filing research assistant with access to three tools:
- search_filings: search for UCC filings by debtor name, state, or status
- get_filing_details: get full details for a specific filing number
- summarize_text: summarize a collateral description into plain English

When researching a filing, follow the natural chain:
1. Search for the filing first
2. Get detailed information using the filing number from search results
3. Summarize the collateral description if the user wants plain English

Always explain your findings clearly after gathering the information.`;

// =============================================================================
// OBSERVATION HELPERS (complete -- do not modify)
// =============================================================================

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
  let resultStr = JSON.stringify(result, null, 2);
  if (resultStr.length > 500) {
    resultStr = resultStr.substring(0, 500) + "\n  ... (truncated)";
  }
  console.log(`\n${"─".repeat(60)}`);
  console.log("[TOOL RESULT]");
  console.log(resultStr);
  console.log("─".repeat(60));
}

// =============================================================================
// YOUR CODE: Implement the chaining-aware agent loop
// =============================================================================

async function runAgent(userMessage) {
  /**
   * Run the agent loop that supports multi-turn tool chaining.
   *
   * The chain pattern:
   *     Turn 1: Claude calls search_filings -> gets results
   *     Turn 2: Claude calls get_filing_details (using filing number from Turn 1)
   *     Turn 3: Claude calls summarize_text (using collateral from Turn 2)
   *     Turn 4: Claude responds with final text (end_turn)
   *
   * Each turn may have ONE or MORE tool calls. Claude decides what to call
   * based on what it learned from previous tool results.
   *
   * Returns Claude's final text response.
   */
  observe("QUERY", userMessage);

  // ------------------------------------------------------------------
  // TODO 1: Initialize messages and tracking variables
  //   const messages = [{ role: "user", content: userMessage }];
  //   let totalToolCalls = 0;
  //   const chainSteps = [];  // Track which tools were called in order
  // ------------------------------------------------------------------
  const messages = [{ role: "user", content: userMessage }];
  let totalToolCalls = 0;
  const chainSteps = [];

  let turn = 0;
  while (turn < MAX_TURNS) {
    turn++;
    observe(
      "THINKING",
      `Turn ${turn} -- sending ${messages.length} message(s) to Claude...`
    );

    // --------------------------------------------------------------
    // TODO 2: Call the Claude API with tools (remember to await)
    //   const response = await client.messages.create({
    //       model: MODEL, max_tokens: 2048, system: SYSTEM_PROMPT,
    //       tools: TOOLS, messages,
    //   });
    // --------------------------------------------------------------

    // --------------------------------------------------------------
    // TODO 3: Handle stop_reason === "tool_use"
    //   - Loop through response.content for tool_use blocks
    //   - Log each with observeToolCall
    //   - Execute using TOOL_FUNCTIONS[block.name](block.input)
    //   - Log with observeToolResult
    //   - Collect toolResults for the response
    //   - Push the tool name to chainSteps
    //   - Push assistant message and tool results to messages
    //   - Update totalToolCalls
    //
    // KEY INSIGHT: In a chain, each turn typically has ONE tool call.
    // Claude uses the result to decide what to call next. The chain
    // emerges from Claude's reasoning, not from your code.
    // --------------------------------------------------------------

    // --------------------------------------------------------------
    // TODO 4: Handle stop_reason === "end_turn"
    //   - Extract text from response.content
    //   - Print chain summary:
    //     const chainStr = chainSteps.length > 0 ? chainSteps.join(" -> ") : "(no tools)";
    //     console.log(`\n[CHAIN] Total tool calls: ${totalToolCalls} ` +
    //                 `across ${turn} turns (${chainStr})`);
    //   - observe("RESPONSE", finalText)
    //   - Return finalText
    // --------------------------------------------------------------

    // Remove this line once you implement the above:
    return "";
  }

  observe("ERROR", `Agent exceeded maximum turns (${MAX_TURNS})`);
  return "Error: Agent exceeded maximum number of turns.";
}

// =============================================================================
// MAIN
// =============================================================================

console.log("=".repeat(60));
console.log("M06 Lab - Step 2: Sequential Tool Chain");
console.log("=".repeat(60));

// Test 1: Full 3-step chain (search -> details -> summarize)
console.log("\n\n>>> Test 1: Full 3-step chain");
const result1 = await runAgent(
  "Find filings for Greenfield Logistics and summarize the collateral"
);
console.log(`\nFINAL ANSWER: ${result1}`);

// Test 2: 2-step chain (details -> summarize)
console.log("\n\n>>> Test 2: 2-step chain");
const result2 = await runAgent(
  "Get details on filing UCC-2024-001 and summarize it"
);
console.log(`\nFINAL ANSWER: ${result2}`);

// Test 3: Single tool, no chain
console.log("\n\n>>> Test 3: Single tool, no chain");
const result3 = await runAgent("Search for filings in New York");
console.log(`\nFINAL ANSWER: ${result3}`);
