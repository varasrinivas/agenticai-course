/**
 * UCC Production Agent — Node.js entry point.
 *
 * This is a simplified Node.js equivalent demonstrating the same
 * architecture: routing, specialist agents, memory, and observability.
 *
 * Run:
 *   node main.js                    # Interactive mode
 *   node main.js --query "..."      # Single query mode
 *
 * Requires: npm install @anthropic-ai/sdk readline
 */

import Anthropic from "@anthropic-ai/sdk";
import * as readline from "readline";

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------
const client = new Anthropic();

const MODEL_TIERS = {
  fast: { modelId: "claude-sonnet-4-20250514", inputCostPer1k: 0.003, outputCostPer1k: 0.015 },
  balanced: { modelId: "claude-sonnet-4-20250514", inputCostPer1k: 0.003, outputCostPer1k: 0.015 },
  powerful: { modelId: "claude-sonnet-4-20250514", inputCostPer1k: 0.003, outputCostPer1k: 0.015 },
};

const TASK_KEYWORDS = {
  filing_lookup: ["filing", "filings", "ucc-1", "ucc-3", "lien", "search", "lookup", "status", "amendment"],
  entity_resolution: ["entity", "company", "match", "resolve", "same company", "related", "subsidiary", "dba"],
  risk_assessment: ["risk", "exposure", "collateral", "lien risk", "assess", "blanket lien", "priority"],
};

// ---------------------------------------------------------------------------
// Simplified UCC filings (subset for Node.js demo)
// ---------------------------------------------------------------------------
const UCC_FILINGS = {
  NY: {
    "NY-2023-0558291": {
      filing_number: "NY-2023-0558291", state: "NY", filing_type: "UCC-1",
      filing_date: "2023-07-18", lapse_date: "2028-07-18",
      debtor_name: "Acme Corporation", debtor_ein: "94-3829471",
      secured_party: "Manhattan Commercial Finance",
      collateral: "Accounts receivable, contract rights, and general intangibles",
      status: "active",
    },
    "NY-2022-0341829": {
      filing_number: "NY-2022-0341829", state: "NY", filing_type: "UCC-1",
      filing_date: "2022-12-05", lapse_date: "2027-12-05",
      debtor_name: "Pinnacle Systems International", debtor_ein: "95-7712034",
      secured_party: "JPMorgan Chase Commercial Banking",
      collateral: "All inventory, equipment, accounts, chattel paper, instruments, and general intangibles",
      status: "active",
    },
  },
  CA: {
    "CA-2023-0847291": {
      filing_number: "CA-2023-0847291", state: "CA", filing_type: "UCC-1",
      filing_date: "2023-03-15", lapse_date: "2028-03-15",
      debtor_name: "Acme Corp", debtor_ein: "94-3829471",
      secured_party: "Pacific Commerce Bank",
      collateral: "All inventory, equipment, accounts receivable, and general intangibles",
      status: "active",
    },
  },
};

// ---------------------------------------------------------------------------
// Tool definitions
// ---------------------------------------------------------------------------
const TOOLS = [
  {
    name: "search_filings",
    description: "Search UCC filings by debtor name and/or state.",
    input_schema: {
      type: "object",
      properties: {
        debtor_name: { type: "string", description: "Debtor name to search" },
        state: { type: "string", description: "Two-letter state code" },
      },
      required: [],
    },
  },
  {
    name: "get_filing_details",
    description: "Get full details for a specific filing by number.",
    input_schema: {
      type: "object",
      properties: {
        filing_number: { type: "string", description: "The filing number" },
      },
      required: ["filing_number"],
    },
  },
];

// ---------------------------------------------------------------------------
// Tool execution
// ---------------------------------------------------------------------------
function executeTool(toolName, toolInput) {
  if (toolName === "search_filings") {
    const results = [];
    const name = (toolInput.debtor_name || "").toLowerCase();
    const stateFilter = toolInput.state ? toolInput.state.toUpperCase() : null;

    for (const [state, filings] of Object.entries(UCC_FILINGS)) {
      if (stateFilter && state !== stateFilter) continue;
      for (const filing of Object.values(filings)) {
        if (!name || filing.debtor_name.toLowerCase().includes(name)) {
          results.push({
            filing_number: filing.filing_number,
            state: filing.state,
            debtor_name: filing.debtor_name,
            secured_party: filing.secured_party,
            status: filing.status,
          });
        }
      }
    }
    return results.length > 0 ? results : [{ message: "No filings found." }];
  }

  if (toolName === "get_filing_details") {
    const num = toolInput.filing_number;
    const state = num.substring(0, 2).toUpperCase();
    if (UCC_FILINGS[state] && UCC_FILINGS[state][num]) {
      return UCC_FILINGS[state][num];
    }
    return { error: `Filing ${num} not found.` };
  }

  return { error: `Unknown tool: ${toolName}` };
}

// ---------------------------------------------------------------------------
// Query classification
// ---------------------------------------------------------------------------
function classifyQuery(query) {
  const lower = query.toLowerCase();
  let bestType = "filing_lookup";
  let bestScore = 0;

  for (const [taskType, keywords] of Object.entries(TASK_KEYWORDS)) {
    const matches = keywords.filter((kw) => lower.includes(kw)).length;
    const score = matches / keywords.length;
    if (score > bestScore) {
      bestScore = score;
      bestType = taskType;
    }
  }
  return { taskType: bestType, confidence: bestScore };
}

// ---------------------------------------------------------------------------
// Agent loop
// ---------------------------------------------------------------------------
async function processQuery(query) {
  const startTime = Date.now();
  const classification = classifyQuery(query);

  const systemPrompt =
    "You are a UCC filing analysis agent. Use the provided tools to answer questions about UCC filings, entities, and lien risk.";

  const messages = [{ role: "user", content: query }];
  const toolCallsMade = [];

  for (let i = 0; i < 10; i++) {
    const response = await client.messages.create({
      model: MODEL_TIERS.balanced.modelId,
      max_tokens: 4096,
      system: systemPrompt,
      tools: TOOLS,
      messages,
    });

    if (response.stop_reason === "tool_use") {
      messages.push({ role: "assistant", content: response.content });
      const toolResults = [];

      for (const block of response.content) {
        if (block.type === "tool_use") {
          toolCallsMade.push({ name: block.name, input: block.input });
          const result = executeTool(block.name, block.input);
          toolResults.push({
            type: "tool_result",
            tool_use_id: block.id,
            content: JSON.stringify(result),
          });
        }
      }
      messages.push({ role: "user", content: toolResults });
    } else {
      let answer = "";
      for (const block of response.content) {
        if (block.type === "text") answer += block.text;
      }
      const elapsedMs = Date.now() - startTime;
      return {
        answer,
        taskType: classification.taskType,
        toolCallsMade,
        latencyMs: elapsedMs,
      };
    }
  }

  return { answer: "Max iterations reached.", taskType: classification.taskType, toolCallsMade, latencyMs: Date.now() - startTime };
}

// ---------------------------------------------------------------------------
// CLI
// ---------------------------------------------------------------------------
async function main() {
  const args = process.argv.slice(2);

  if (args.includes("--query")) {
    const idx = args.indexOf("--query");
    const query = args[idx + 1];
    if (!query) {
      console.error("Usage: node main.js --query \"your question\"");
      process.exit(1);
    }
    console.log(`Query: ${query}\n`);
    const result = await processQuery(query);
    console.log(`Answer: ${result.answer}`);
    console.log(`\n  [Task: ${result.taskType} | Latency: ${result.latencyMs}ms | Tools: ${result.toolCallsMade.map((t) => t.name).join(", ")}]`);
    return;
  }

  // Interactive mode
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });

  console.log("=".repeat(60));
  console.log("  UCC Production Agent (Node.js) -- Interactive Mode");
  console.log("  Type 'quit' to exit");
  console.log("=".repeat(60));
  console.log();

  const ask = () => {
    rl.question("You: ", async (query) => {
      query = query.trim();
      if (!query || query.toLowerCase() === "quit") {
        console.log("Goodbye!");
        rl.close();
        return;
      }

      console.log("\nProcessing...\n");
      try {
        const result = await processQuery(query);
        console.log(`Agent: ${result.answer}`);
        console.log(`\n  [Task: ${result.taskType} | Latency: ${result.latencyMs}ms]\n`);
      } catch (err) {
        console.error(`Error: ${err.message}\n`);
      }
      ask();
    });
  };

  ask();
}

main().catch(console.error);
