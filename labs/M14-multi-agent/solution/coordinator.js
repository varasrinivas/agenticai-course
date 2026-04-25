/**
 * M14 Lab -- Multi-Agent Systems: All-in-One Coordinator (Node.js Solution)
 * =========================================================================
 * 4-agent content pipeline for UCC filing research:
 *   Researcher -> Analyst -> Writer -> Reviewer
 *
 * Usage:
 *   node coordinator.js
 *   node coordinator.js "Greenfield Logistics"
 *
 * Requires:
 *   npm install @anthropic-ai/sdk dotenv
 */

import Anthropic from "@anthropic-ai/sdk";
import { config } from "dotenv";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { readFileSync } from "fs";

config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const client = new Anthropic();
const MODEL = "claude-sonnet-4-20250514";

// =============================================================================
// MOCK DATA — inline version of shared/mock_ucc_data.py
// =============================================================================

const MOCK_FILINGS = [
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
      "Specific equipment: (3) Caterpillar 349F L hydraulic excavators, serial numbers CAT349F-8821, CAT349F-8822, CAT349F-8823; (1) Liebherr LTM 1300-6.2 mobile crane, serial number LTM-DE-90124.",
    filing_office: "TX Secretary of State",
    document_number: "DOC-TX-2023-71092",
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
];

// =============================================================================
// TOOL FUNCTIONS
// =============================================================================

function searchFilings(debtorName, state) {
  let results = [...MOCK_FILINGS];
  if (debtorName) {
    const query = debtorName.toLowerCase();
    results = results.filter((f) =>
      f.debtor.name.toLowerCase().includes(query)
    );
  }
  if (state) {
    const query = state.toLowerCase();
    results = results.filter((f) => f.state.toLowerCase() === query);
  }
  return results.map((f) => ({
    filing_number: f.filing_number,
    debtor: f.debtor.name,
    secured_party: f.secured_party.name,
    state: f.state,
    status: f.status,
    type: f.type,
    filing_date: f.filing_date,
    collateral: f.collateral_description.substring(0, 150) + "...",
  }));
}

function getFilingDetails(filingNumber) {
  const filing = MOCK_FILINGS.find(
    (f) => f.filing_number === filingNumber
  );
  return filing || { error: `Filing ${filingNumber} not found` };
}

function calculateRisk(debtorName) {
  const filings = MOCK_FILINGS.filter((f) =>
    f.debtor.name.toLowerCase().includes(debtorName.toLowerCase())
  );
  if (filings.length === 0) {
    return {
      debtor: debtorName,
      risk_score: 0,
      risk_level: "UNKNOWN",
      message: `No filings found for '${debtorName}'`,
    };
  }
  const active = filings.filter((f) => f.status === "Active");
  const blanket = filings.filter(
    (f) =>
      f.collateral_description.toLowerCase().includes("all assets") ||
      f.collateral_description.toLowerCase().includes("all accounts")
  );
  const score = Math.min(1.0, active.length * 0.25 + blanket.length * 0.3);
  let level, rec;
  if (score >= 0.7) {
    level = "HIGH";
    rec = "Significant lien exposure. Detailed due diligence recommended.";
  } else if (score >= 0.4) {
    level = "MEDIUM";
    rec = "Moderate lien activity. Review collateral descriptions.";
  } else {
    level = "LOW";
    rec = "Limited lien exposure. Standard credit procedures should suffice.";
  }
  return {
    debtor: debtorName,
    risk_score: Math.round(score * 100) / 100,
    risk_level: level,
    total_filings: filings.length,
    active_filings: active.length,
    blanket_liens: blanket.length,
    recommendation: rec,
  };
}

function executeTool(toolName, toolInput) {
  try {
    if (toolName === "search_filings") {
      return JSON.stringify(
        searchFilings(toolInput.debtor_name, toolInput.state),
        null,
        2
      );
    } else if (toolName === "get_filing_details") {
      return JSON.stringify(getFilingDetails(toolInput.filing_number), null, 2);
    } else if (toolName === "calculate_risk") {
      return JSON.stringify(calculateRisk(toolInput.debtor_name), null, 2);
    }
    return JSON.stringify({ error: `Unknown tool: ${toolName}` });
  } catch (e) {
    return JSON.stringify({ error: `Tool failed: ${e.message}` });
  }
}

// =============================================================================
// TOOL SCHEMAS
// =============================================================================

const RESEARCH_TOOLS = [
  {
    name: "search_filings",
    description: "Search UCC filings by debtor name and/or state.",
    input_schema: {
      type: "object",
      properties: {
        debtor_name: {
          type: "string",
          description: "Debtor name to search for",
        },
        state: { type: "string", description: "State filter" },
      },
      required: [],
    },
  },
  {
    name: "get_filing_details",
    description: "Get full details of a specific UCC filing.",
    input_schema: {
      type: "object",
      properties: {
        filing_number: {
          type: "string",
          description: "The filing number",
        },
      },
      required: ["filing_number"],
    },
  },
];

const ANALYSIS_TOOLS = [
  {
    name: "calculate_risk",
    description: "Calculate risk profile for a debtor.",
    input_schema: {
      type: "object",
      properties: {
        debtor_name: {
          type: "string",
          description: "Debtor name",
        },
      },
      required: ["debtor_name"],
    },
  },
];

// =============================================================================
// OBSERVATION HELPERS
// =============================================================================

function observe(label, message) {
  console.log(`\n${"=".repeat(60)}`);
  console.log(`[${label}] ${message}`);
  console.log("=".repeat(60));
}

function observeHandoff(from, to, dataSize) {
  console.log(`\n${"─".repeat(60)}`);
  console.log(`[HANDOFF] ${from} -> ${to} (${dataSize.toLocaleString()} chars)`);
  console.log("─".repeat(60));
}

function observePhase(num, total, desc) {
  console.log(`\n${"*".repeat(60)}`);
  console.log(`[PHASE ${num}/${total}] ${desc}`);
  console.log("*".repeat(60));
}

// =============================================================================
// SUBAGENT RUNNER
// =============================================================================

async function runSubagent(agentName, systemPrompt, task, tools, maxTurns = 5) {
  console.log(`\n[${agentName}] Starting...`);

  const messages = [{ role: "user", content: task }];

  // No tools — single call
  if (!tools || tools.length === 0) {
    const response = await client.messages.create({
      model: MODEL,
      max_tokens: 4096,
      system: systemPrompt,
      messages,
    });
    let text = "";
    for (const block of response.content) {
      if (block.type === "text") text += block.text;
    }
    console.log(`[${agentName}] Complete (${text.length} chars)`);
    return text;
  }

  // With tools — ReAct loop
  for (let turn = 0; turn < maxTurns; turn++) {
    const response = await client.messages.create({
      model: MODEL,
      max_tokens: 4096,
      system: systemPrompt,
      tools,
      messages,
    });

    if (response.stop_reason !== "tool_use") {
      let text = "";
      for (const block of response.content) {
        if (block.type === "text") text += block.text;
      }
      console.log(`[${agentName}] Complete (${text.length} chars, ${turn + 1} turn(s))`);
      return text;
    }

    const toolResults = [];
    for (const block of response.content) {
      if (block.type === "tool_use") {
        console.log(
          `[${agentName}] Calling: ${block.name}(${JSON.stringify(block.input)})`
        );
        const result = executeTool(block.name, block.input);
        toolResults.push({
          type: "tool_result",
          tool_use_id: block.id,
          content: result,
        });
      }
    }

    messages.push({ role: "assistant", content: response.content });
    messages.push({ role: "user", content: toolResults });
  }

  return `${agentName} did not complete within ${maxTurns} turns.`;
}

// =============================================================================
// SPECIALIST AGENTS
// =============================================================================

const RESEARCHER_PROMPT = `You are a UCC filing researcher. Your ONLY job is to search for
and gather raw filing data for a given entity.

Use search_filings to find all filings, then get_filing_details for each one.
Return a JSON object: {"entity": "...", "total_found": N, "filings": [...]}
Include: filing_number, type, state, status, filing_date, secured_party, collateral_summary.
ALWAYS use tools. Never guess or make up filing data.`;

const ANALYST_PROMPT = `You are a UCC filing analyst. You receive research data and identify
patterns, risks, and key insights. Use calculate_risk for quantitative scores.

Look for: multi-state exposure, blanket liens, secured party concentration, filing freshness.
Return a JSON object: {"entity": "...", "risk_score": N, "risk_level": "...",
  "patterns": [...], "summary": "...", "recommendation": "..."}`;

const WRITER_PROMPT = `You are a professional report writer for UCC lien analysis.
Format: # UCC Lien Risk Report: [Entity]
Sections: Executive Summary, Filing Details, Risk Assessment, Recommendation.
ONLY use data provided. Never fabricate filing numbers.`;

const REVIEWER_PROMPT = `You are a quality reviewer for UCC filing reports.
Check: filing number accuracy, data consistency, no fabrication, completeness.
Return: VERDICT: APPROVED or VERDICT: NEEDS_REVISION with issues.`;

async function runResearcher(entityName) {
  return await runSubagent(
    "Researcher",
    RESEARCHER_PROMPT,
    `Find all UCC filings for '${entityName}'. Search across all states.`,
    RESEARCH_TOOLS,
    10
  );
}

async function runAnalyst(findingsJson) {
  let entity = "Unknown";
  try {
    entity = JSON.parse(findingsJson).entity || "Unknown";
  } catch {}

  return await runSubagent(
    "Analyst",
    ANALYST_PROMPT,
    `Analyze UCC filing data for '${entity}'.\n\n## Research Data\n${findingsJson}`,
    ANALYSIS_TOOLS,
    5
  );
}

async function runWriter(findingsJson, analysisJson) {
  return await runSubagent(
    "Writer",
    WRITER_PROMPT,
    `Write a UCC Lien Risk Report.\n\n## Research Findings\n${findingsJson}\n\n## Analysis\n${analysisJson}`,
    null
  );
}

async function runReviewer(report, findingsJson) {
  return await runSubagent(
    "Reviewer",
    REVIEWER_PROMPT,
    `Review this report for accuracy.\n\n## Report\n${report}\n\n## Source Data\n${findingsJson}`,
    null
  );
}

// =============================================================================
// COORDINATOR
// =============================================================================

async function runPipeline(entityName) {
  const startTime = Date.now();
  observe("COORDINATOR", `Starting pipeline for: ${entityName}`);

  // Phase 1: Research
  observePhase(1, 4, "Research — Gathering UCC filings");
  let researchData;
  try {
    researchData = await runResearcher(entityName);
  } catch (e) {
    observe("ERROR", `Researcher failed: ${e.message}`);
    return `Pipeline failed at Research phase: ${e.message}`;
  }
  observeHandoff("Researcher", "Analyst", researchData.length);

  // Check for empty results
  try {
    const parsed = JSON.parse(researchData);
    if (parsed.total_found === 0) {
      observe("COORDINATOR", `No filings found for '${entityName}'.`);
      return `No UCC filings found for '${entityName}'. Pipeline complete.`;
    }
  } catch {
    // Non-JSON response, continue anyway
  }

  // Phase 2: Analysis
  observePhase(2, 4, "Analysis — Identifying patterns and risk");
  let analysis;
  try {
    analysis = await runAnalyst(researchData);
  } catch (e) {
    observe("ERROR", `Analyst failed: ${e.message}`);
    return `Pipeline failed at Analysis phase: ${e.message}`;
  }
  observeHandoff("Analyst", "Writer", analysis.length);

  // Phase 3: Writing
  observePhase(3, 4, "Writing — Generating risk report");
  let report;
  try {
    report = await runWriter(researchData, analysis);
  } catch (e) {
    observe("ERROR", `Writer failed: ${e.message}`);
    return `Pipeline failed at Writing phase: ${e.message}`;
  }
  observeHandoff("Writer", "Reviewer", report.length);

  // Phase 4: Review
  observePhase(4, 4, "Review — Verifying accuracy");
  let review;
  try {
    review = await runReviewer(report, researchData);
  } catch (e) {
    observe("ERROR", `Reviewer failed: ${e.message}`);
    review = "VERDICT: REVIEW_SKIPPED\nNOTES: Reviewer agent encountered an error.";
  }

  const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
  observe("COORDINATOR", `Pipeline complete in ${elapsed}s`);

  return `${report}\n\n${"=".repeat(60)}\nREVIEW\n${"=".repeat(60)}\n${review}\n\n${"=".repeat(60)}\nPipeline Stats: 4 agents | ${elapsed}s total\n${"=".repeat(60)}`;
}

// =============================================================================
// MAIN
// =============================================================================

const entityArg = process.argv[2] || "Acme Corporation";

console.log("=".repeat(60));
console.log("M14 Lab — Multi-Agent Content Pipeline (Node.js SOLUTION)");
console.log("=".repeat(60));
console.log(`Entity: ${entityArg}`);
console.log("=".repeat(60));

const result = await runPipeline(entityArg);

console.log("\n" + "=".repeat(60));
console.log("FINAL REPORT");
console.log("=".repeat(60));
console.log(result);
