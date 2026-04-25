/**
 * M12 -- ReAct Agent (Complete Solution -- Node.js)
 * ===================================================
 * A ReAct research agent with 3 UCC filing tools, query router, and trace logging.
 *
 * Usage:
 *   node react_agent.js                  # Run test queries with ReAct loop
 *   node react_agent.js --router         # Run with query router
 *   node react_agent.js --trace          # Run with formatted trace output
 *   node react_agent.js --router --trace # Both router and trace
 *
 * Prerequisites:
 *   npm install @anthropic-ai/sdk dotenv
 */

import Anthropic from "@anthropic-ai/sdk";
import { config } from "dotenv";
import { readFileSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

config(); // load .env

const __dirname = dirname(fileURLToPath(import.meta.url));

// ---------------------------------------------------------------------------
// Load mock data from shared Python-compatible JSON
// ---------------------------------------------------------------------------
// We inline the mock data here since the shared data is in Python format.
// In a real project you'd use a shared JSON file or database.

const ALL_FILINGS = [
  {
    filing_number: "UCC-2024-NY-0012847",
    type: "UCC-1",
    state: "New York",
    filing_date: "2024-03-15",
    expiration_date: "2029-03-15",
    status: "Active",
    debtor: {
      name: "Greenfield Logistics LLC",
      address: "450 West 33rd Street, Suite 800, New York, NY 10001",
      org_type: "LLC",
      jurisdiction: "New York",
    },
    secured_party: {
      name: "Atlantic Capital Partners",
      address: "1 Chase Manhattan Plaza, Floor 45, New York, NY 10005",
    },
    collateral_description:
      "All accounts receivable, inventory, equipment, and general intangibles now owned or hereafter acquired by Debtor.",
    filing_office: "NY Department of State",
    document_number: "DOC-NY-2024-88291",
  },
  {
    filing_number: "UCC-2024-CA-0098231",
    type: "UCC-1",
    state: "California",
    filing_date: "2024-01-22",
    expiration_date: "2029-01-22",
    status: "Active",
    debtor: {
      name: "Pacific Ridge Technologies Inc",
      address: "2800 Sand Hill Road, Menlo Park, CA 94025",
      org_type: "Corporation",
      jurisdiction: "Delaware",
    },
    secured_party: {
      name: "Silicon Valley Bank (a division of First Citizens BancShares)",
      address: "3003 Tasman Drive, Santa Clara, CA 95054",
    },
    collateral_description:
      "All assets of the Debtor including but not limited to: intellectual property, patents, trademarks, accounts, deposit accounts, investment property, and all proceeds thereof.",
    filing_office: "CA Secretary of State",
    document_number: "DOC-CA-2024-44019",
  },
  {
    filing_number: "UCC-2023-TX-0187634",
    type: "UCC-1",
    state: "Texas",
    filing_date: "2023-09-10",
    expiration_date: "2028-09-10",
    status: "Active",
    debtor: {
      name: "Lone Star Energy Solutions LP",
      address: "1200 Smith Street, Suite 3000, Houston, TX 77002",
      org_type: "Limited Partnership",
      jurisdiction: "Texas",
    },
    secured_party: {
      name: "Wells Fargo Equipment Finance",
      address: "301 South College Street, Charlotte, NC 28202",
    },
    collateral_description:
      'Specific equipment: (3) Caterpillar 349F L hydraulic excavators, serial numbers CAT349F-8821, CAT349F-8822, CAT349F-8823; (1) Liebherr LTM 1300-6.2 mobile crane, serial number LTM-DE-90124.',
    filing_office: "TX Secretary of State",
    document_number: "DOC-TX-2023-71092",
  },
  {
    filing_number: "UCC-2024-FL-0054219",
    type: "UCC-3",
    state: "Florida",
    filing_date: "2024-06-01",
    expiration_date: "2027-11-18",
    status: "Amendment",
    debtor: {
      name: "Sunshine Medical Group PA",
      address: "4500 Biscayne Boulevard, Miami, FL 33137",
      org_type: "Professional Association",
      jurisdiction: "Florida",
    },
    secured_party: {
      name: "TD Bank N.A.",
      address: "1701 Route 70 East, Cherry Hill, NJ 08034",
    },
    collateral_description:
      "Amendment to add: medical equipment including (2) Siemens MAGNETOM Vida 3T MRI systems and (1) GE Revolution CT scanner. Original collateral description unchanged.",
    filing_office: "FL Secured Transaction Registry",
    document_number: "DOC-FL-2024-22817",
    original_filing: "UCC-2022-FL-0031456",
  },
  {
    filing_number: "UCC-2022-DE-0002914",
    type: "UCC-1",
    state: "Delaware",
    filing_date: "2022-04-30",
    expiration_date: "2027-04-30",
    status: "Active",
    debtor: {
      name: "Nextera Holdings Corp",
      address: "1209 Orange Street, Wilmington, DE 19801",
      org_type: "Corporation",
      jurisdiction: "Delaware",
    },
    secured_party: {
      name: "JPMorgan Chase Bank N.A.",
      address: "383 Madison Avenue, New York, NY 10179",
    },
    collateral_description:
      "All assets of the Debtor, whether now owned or hereafter acquired, including without limitation all accounts, chattel paper, commercial tort claims, deposit accounts, documents, equipment, fixtures, general intangibles, goods, instruments, inventory, investment property, letter-of-credit rights, letters of credit, money, oil, gas, and other minerals, and all proceeds and products thereof.",
    filing_office: "DE Division of Corporations",
    document_number: "DOC-DE-2022-09381",
  },
  {
    filing_number: "UCC-2024-IL-0076543",
    type: "UCC-1",
    state: "Illinois",
    filing_date: "2024-02-14",
    expiration_date: "2029-02-14",
    status: "Active",
    debtor: {
      name: "Midwest Agricultural Cooperative",
      address: "200 W Adams St, Suite 1500, Chicago, IL 60606",
      org_type: "Cooperative",
      jurisdiction: "Illinois",
    },
    secured_party: {
      name: "Farm Credit Services of America",
      address: "5015 S 118th St, Omaha, NE 68137",
    },
    collateral_description:
      "All farm products, including but not limited to crops (corn, soybeans, wheat), livestock, and farm equipment. All accounts and proceeds arising from the sale of farm products.",
    filing_office: "IL Secretary of State",
    document_number: "DOC-IL-2024-33901",
  },
  {
    filing_number: "UCC-2023-NY-0145678",
    type: "UCC-3",
    state: "New York",
    filing_date: "2023-12-01",
    expiration_date: null,
    status: "Terminated",
    debtor: {
      name: "Harbor Shipping International Inc",
      address: "One World Trade Center, Floor 72, New York, NY 10007",
      org_type: "Corporation",
      jurisdiction: "New York",
    },
    secured_party: {
      name: "Citibank N.A.",
      address: "388 Greenwich Street, New York, NY 10013",
    },
    collateral_description:
      "TERMINATION -- This filing terminates the effectiveness of the original filing UCC-2019-NY-0089012.",
    filing_office: "NY Department of State",
    document_number: "DOC-NY-2023-99102",
    original_filing: "UCC-2019-NY-0089012",
  },
  {
    filing_number: "UCC-2024-GA-0034521",
    type: "UCC-1",
    state: "Georgia",
    filing_date: "2024-04-20",
    expiration_date: "2029-04-20",
    status: "Active",
    debtor: {
      name: "Peachtree Ventures LLC",
      address: "3344 Peachtree Road NE, Suite 1200, Atlanta, GA 30326",
      org_type: "LLC",
      jurisdiction: "Georgia",
    },
    secured_party: {
      name: "Truist Financial Corporation",
      address: "214 N Tryon Street, Charlotte, NC 28202",
    },
    collateral_description:
      "All inventory held at debtor's warehouse locations in Fulton, DeKalb, and Gwinnett counties, Georgia. All accounts receivable generated from wholesale distribution operations.",
    filing_office: "GA Superior Court Clerks' Cooperative Authority",
    document_number: "DOC-GA-2024-18723",
  },
  // Edge case filings
  {
    filing_number: "UCC-2024-NV-0000001",
    type: "UCC-1",
    state: "Nevada",
    filing_date: "2024-05-01",
    expiration_date: "2029-05-01",
    status: "Active",
    debtor: {
      name: "",
      address: "100 N Carson St, Carson City, NV 89701",
      org_type: "LLC",
      jurisdiction: "Nevada",
    },
    secured_party: {
      name: "Quick Lend Corp",
      address: "555 E Washington Ave, Las Vegas, NV 89101",
    },
    collateral_description: "All assets.",
    filing_office: "NV Secretary of State",
    document_number: "DOC-NV-2024-00001",
  },
  {
    filing_number: "UCC-2024-NY-0012847-DUP",
    type: "UCC-1",
    state: "New York",
    filing_date: "2024-07-10",
    expiration_date: "2029-07-10",
    status: "Active",
    debtor: {
      name: "Greenfield Logistics LLC",
      address: "450 West 33rd Street, Suite 800, New York, NY 10001",
      org_type: "LLC",
      jurisdiction: "New York",
    },
    secured_party: {
      name: "Second National Bank",
      address: "200 Park Avenue, New York, NY 10166",
    },
    collateral_description: "All inventory and equipment.",
    filing_office: "NY Department of State",
    document_number: "DOC-NY-2024-92104",
  },
  {
    filing_number: "UCC-2019-OH-0299100",
    type: "UCC-1",
    state: "Ohio",
    filing_date: "2019-03-01",
    expiration_date: "2024-03-01",
    status: "Lapsed",
    debtor: {
      name: "Buckeye Manufacturing Co",
      address: "75 E State Street, Columbus, OH 43215",
      org_type: "Corporation",
      jurisdiction: "Ohio",
    },
    secured_party: {
      name: "KeyBank National Association",
      address: "127 Public Square, Cleveland, OH 44114",
    },
    collateral_description:
      "All equipment located at 900 Industrial Parkway, Akron, OH 44301.",
    filing_office: "OH Secretary of State",
    document_number: "DOC-OH-2019-45021",
  },
];

// ---------------------------------------------------------------------------
// Tool implementations
// ---------------------------------------------------------------------------
function searchFilings(debtorName = null, state = null) {
  try {
    let results = [...ALL_FILINGS];
    if (debtorName) {
      const lower = debtorName.toLowerCase();
      results = results.filter((f) =>
        f.debtor.name.toLowerCase().includes(lower)
      );
    }
    if (state) {
      const lower = state.toLowerCase();
      results = results.filter((f) => f.state.toLowerCase() === lower);
    }
    const summaries = results.map((f) => ({
      filing_number: f.filing_number,
      debtor: f.debtor.name,
      state: f.state,
      status: f.status,
      filing_date: f.filing_date,
      type: f.type,
    }));
    return { success: true, count: summaries.length, results: summaries };
  } catch (e) {
    return { success: false, error: e.message, count: 0, results: [] };
  }
}

function getFilingDetails(filingNumber) {
  try {
    const filing = ALL_FILINGS.find((f) => f.filing_number === filingNumber);
    if (!filing) {
      return {
        success: false,
        error: `Filing '${filingNumber}' not found`,
        filing: null,
      };
    }
    return { success: true, filing };
  } catch (e) {
    return { success: false, error: e.message, filing: null };
  }
}

function calculateRisk(debtorName) {
  try {
    const lower = debtorName.toLowerCase();
    const filings = ALL_FILINGS.filter((f) =>
      f.debtor.name.toLowerCase().includes(lower)
    );
    if (filings.length === 0) {
      return {
        success: false,
        error: `No filings found for '${debtorName}'`,
        risk_score: null,
        risk_level: null,
        factors: [],
      };
    }

    let score = 0.0;
    const factors = [];

    // Factor 1: Active filing count
    const active = filings.filter((f) => f.status === "Active");
    const activeContribution = active.length * 0.15;
    score += activeContribution;
    factors.push(
      `${active.length} active filing(s): +${activeContribution.toFixed(2)}`
    );

    // Factor 2: Blanket liens
    const blanketKeywords = [
      "all assets",
      "all accounts",
      "now owned or hereafter acquired",
    ];
    let blanketCount = 0;
    for (const f of filings) {
      const desc = (f.collateral_description || "").toLowerCase();
      if (blanketKeywords.some((kw) => desc.includes(kw))) {
        blanketCount++;
      }
    }
    if (blanketCount > 0) {
      score += 0.2;
      factors.push(`${blanketCount} blanket lien(s): +0.20`);
    }

    // Factor 3: Multi-state
    const states = new Set(filings.map((f) => f.state));
    if (states.size > 1) {
      score += 0.1;
      factors.push(`Filings in ${states.size} states: +0.10`);
    }

    // Factor 4: Multiple secured parties
    const parties = new Set(filings.map((f) => f.secured_party.name));
    if (parties.size > 1) {
      score += 0.1;
      factors.push(`${parties.size} distinct secured parties: +0.10`);
    }

    score = Math.min(score, 1.0);
    let level;
    if (score >= 0.7) level = "HIGH";
    else if (score >= 0.4) level = "MEDIUM";
    else level = "LOW";

    return {
      success: true,
      debtor_name: debtorName,
      filings_analyzed: filings.length,
      risk_score: Math.round(score * 100) / 100,
      risk_level: level,
      factors,
    };
  } catch (e) {
    return {
      success: false,
      error: e.message,
      risk_score: null,
      risk_level: null,
      factors: [],
    };
  }
}

// ---------------------------------------------------------------------------
// Tool definitions for Claude API
// ---------------------------------------------------------------------------
const TOOL_DEFINITIONS = [
  {
    name: "search_filings",
    description:
      "Search UCC filings by debtor name and/or state. Returns a summary list of matching filings with filing number, debtor name, state, status, and filing date.",
    input_schema: {
      type: "object",
      properties: {
        debtor_name: {
          type: "string",
          description: "Name (or partial name) of the debtor to search for",
        },
        state: {
          type: "string",
          description: "US state to filter by (e.g. 'New York', 'California')",
        },
      },
      required: [],
    },
  },
  {
    name: "get_filing_details",
    description:
      "Get the full details of a specific UCC filing by its filing number. Returns all fields including collateral description, secured party, and filing office.",
    input_schema: {
      type: "object",
      properties: {
        filing_number: {
          type: "string",
          description:
            "The UCC filing number (e.g. 'UCC-2024-NY-0012847')",
        },
      },
      required: ["filing_number"],
    },
  },
  {
    name: "calculate_risk",
    description:
      "Calculate a risk score (0.0-1.0) for a debtor based on their UCC filing history. Considers number of active filings, blanket liens, multi-state presence, and number of distinct secured parties. Returns risk_score, risk_level (LOW/MEDIUM/HIGH), and contributing factors.",
    input_schema: {
      type: "object",
      properties: {
        debtor_name: {
          type: "string",
          description: "Name of the debtor to assess risk for",
        },
      },
      required: ["debtor_name"],
    },
  },
];

// ---------------------------------------------------------------------------
// Tool dispatcher
// ---------------------------------------------------------------------------
function executeTool(toolName, toolInput) {
  switch (toolName) {
    case "search_filings":
      return searchFilings(toolInput.debtor_name, toolInput.state);
    case "get_filing_details":
      return getFilingDetails(toolInput.filing_number);
    case "calculate_risk":
      return calculateRisk(toolInput.debtor_name);
    default:
      return { success: false, error: `Unknown tool: ${toolName}` };
  }
}

// ---------------------------------------------------------------------------
// Trace logging
// ---------------------------------------------------------------------------
class TraceLog {
  constructor() {
    this.entries = [];
    this.currentTurn = 0;
  }

  newTurn() {
    this.currentTurn++;
  }

  think(text) {
    this.entries.push({ turn: this.currentTurn, type: "THINK", content: text });
  }

  act(toolName, toolInput) {
    const inputStr = Object.entries(toolInput)
      .map(([k, v]) => `${k}="${v}"`)
      .join(", ");
    this.entries.push({
      turn: this.currentTurn,
      type: "ACT",
      content: `${toolName}(${inputStr})`,
    });
  }

  observe(result) {
    let summary;
    if (result && typeof result === "object") {
      if ("count" in result) {
        summary = `[${result.count} result(s) found]`;
      } else if ("risk_score" in result && result.success) {
        summary = `{risk_score: ${result.risk_score}, risk_level: "${result.risk_level}"}`;
      } else if ("filing" in result && result.success) {
        summary = `[Filing ${result.filing.filing_number} -- ${result.filing.debtor.name}]`;
      } else if ("error" in result) {
        summary = `[ERROR: ${result.error}]`;
      } else {
        summary = JSON.stringify(result).slice(0, 120);
      }
    } else {
      summary = String(result).slice(0, 120);
    }
    this.entries.push({
      turn: this.currentTurn,
      type: "OBSERVE",
      content: summary,
    });
  }

  response(text) {
    this.entries.push({
      turn: this.currentTurn,
      type: "RESPONSE",
      content: text.length > 200 ? text.slice(0, 200) + "..." : text,
    });
  }
}

// ---------------------------------------------------------------------------
// ReAct loop
// ---------------------------------------------------------------------------
async function runReactAgent(query, maxTurns = 10) {
  const client = new Anthropic();
  const trace = new TraceLog();
  const messages = [{ role: "user", content: query }];

  console.log(`\n${"=".repeat(60)}`);
  console.log(`QUERY: ${query}`);
  console.log(`${"=".repeat(60)}`);

  for (let turn = 1; turn <= maxTurns; turn++) {
    trace.newTurn();

    // Step 1: Call Claude
    let response;
    try {
      response = await client.messages.create({
        model: "claude-sonnet-4-20250514",
        max_tokens: 4096,
        system: `You are a UCC (Uniform Commercial Code) filing research agent.
You help users investigate UCC filings, assess debtor risk, and answer questions
about commercial liens and secured transactions.

When answering questions:
1. Think step-by-step about what information you need.
2. Use the available tools to gather data before answering.
3. Always cite specific filing numbers and data points in your answers.
4. If a search returns no results, say so clearly -- do not make up data.`,
        tools: TOOL_DEFINITIONS,
        messages,
      });
    } catch (e) {
      const errorMsg = `API error: ${e.message}`;
      console.log(`\n[ERROR] ${errorMsg}`);
      trace.response(errorMsg);
      return { text: errorMsg, trace };
    }

    // Step 2: Extract text blocks as "think"
    for (const block of response.content) {
      if (block.type === "text") {
        trace.think(block.text);
        const preview =
          block.text.length > 150
            ? block.text.slice(0, 150) + "..."
            : block.text;
        console.log(`\n[THINK] Turn ${turn}: ${preview}`);
      }
    }

    // Step 3: Check stop_reason
    if (response.stop_reason === "end_turn") {
      let finalText = "";
      for (const block of response.content) {
        if (block.type === "text") finalText += block.text;
      }
      if (!finalText) finalText = "[No text in final response]";

      trace.response(finalText);
      const preview =
        finalText.length > 300 ? finalText.slice(0, 300) + "..." : finalText;
      console.log(`\n[RESPONSE] ${preview}`);
      return { text: finalText, trace };
    }

    // Step 4: Process tool calls
    messages.push({ role: "assistant", content: response.content });

    const toolResults = [];
    for (const block of response.content) {
      if (block.type === "tool_use") {
        const toolName = block.name;
        const toolInput = block.input;

        trace.act(toolName, toolInput);
        const inputStr = Object.entries(toolInput)
          .map(([k, v]) => `${k}="${v}"`)
          .join(", ");
        console.log(`[ACT]     Turn ${turn}: ${toolName}(${inputStr})`);

        const result = executeTool(toolName, toolInput);

        trace.observe(result);
        if ("count" in result) {
          console.log(`[OBSERVE] Turn ${turn}: ${result.count} result(s)`);
        } else if (result.success && "risk_score" in result) {
          console.log(
            `[OBSERVE] Turn ${turn}: risk_score=${result.risk_score}, level=${result.risk_level}`
          );
        } else if (result.success && "filing" in result) {
          console.log(
            `[OBSERVE] Turn ${turn}: Filing found -- ${result.filing.debtor.name}`
          );
        } else if ("error" in result) {
          console.log(`[OBSERVE] Turn ${turn}: ERROR -- ${result.error}`);
        }

        toolResults.push({
          type: "tool_result",
          tool_use_id: block.id,
          content: JSON.stringify(result),
        });
      }
    }

    messages.push({ role: "user", content: toolResults });
  }

  console.log(`\n[MAX TURNS REACHED (${maxTurns})]`);
  trace.response(`[Max turns reached after ${maxTurns} cycles]`);
  return {
    text: `I wasn't able to complete the research within ${maxTurns} turns.`,
    trace,
  };
}

// ---------------------------------------------------------------------------
// Query Router
// ---------------------------------------------------------------------------
function classifyQuery(query) {
  const lower = query.toLowerCase();

  // Pattern 1: Filing number
  if (/ucc-\d{4}-[a-z]{2}-\d+/i.test(lower)) return "lookup";

  // Pattern 2: Keywords
  const researchKeywords = [
    "risk",
    "assess",
    "compare",
    "analyze",
    "analysis",
    "why",
    "explain",
    "evaluate",
    "recommend",
    "should",
    "how many",
    "which is",
    "what is the risk",
  ];
  const lookupKeywords = ["find", "search", "look up", "list", "show me"];

  const hasResearch = researchKeywords.some((kw) => lower.includes(kw));
  const hasLookup = lookupKeywords.some((kw) => lower.includes(kw));

  if (hasResearch) return "research";
  if (hasLookup) return "lookup";

  return "research";
}

async function runWithRouter(query) {
  const category = classifyQuery(query);
  console.log(`\n[ROUTER] Classified as: ${category.toUpperCase()}`);

  if (category === "lookup") {
    return runReactAgent(query, 3);
  } else {
    return runReactAgent(query, 10);
  }
}

// ---------------------------------------------------------------------------
// Trace formatter
// ---------------------------------------------------------------------------
function formatTrace(trace) {
  return trace.entries
    .map((entry) => {
      const paddedType = entry.type.padEnd(8);
      return `Turn ${entry.turn}: ${paddedType} --> "${entry.content}"`;
    })
    .join("\n");
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------
const TEST_QUERIES = [
  "Find all UCC filings for Greenfield Logistics",
  "What is the risk level for Greenfield Logistics and why?",
  "Get the full details of filing UCC-2024-CA-0098231",
];

async function main() {
  const args = process.argv.slice(2);
  const useRouter = args.includes("--router");
  const showTrace = args.includes("--trace");

  for (const query of TEST_QUERIES) {
    let result;
    if (useRouter) {
      result = await runWithRouter(query);
    } else {
      result = await runReactAgent(query);
    }

    if (showTrace) {
      console.log("\n--- Reasoning Trace ---");
      console.log(formatTrace(result.trace));
      console.log("--- End Trace ---\n");
    } else {
      console.log(`\nFINAL ANSWER:\n${result.text}\n`);
    }
  }
}

main().catch(console.error);
