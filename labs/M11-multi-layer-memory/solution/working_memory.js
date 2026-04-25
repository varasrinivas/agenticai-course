/**
 * M11 Lab - Step 1: Working Memory Scratchpad (Solution)
 * =====================================================
 * Complete solution: key-value working memory that an agent uses
 * to track current task state across tool calls and conversation turns.
 *
 * Usage:
 *     node working_memory.js
 */

import Anthropic from "@anthropic-ai/sdk";
import "dotenv/config";
import { searchFilings, getFilingByNumber } from "../../shared/mock_ucc_data.js";

const client = new Anthropic();
const MODEL = "claude-sonnet-4-20250514";

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
  console.log(`[USING TOOL] ${toolName}`);
  console.log(`[INPUT]      ${JSON.stringify(toolInput, null, 2)}`);
  console.log("─".repeat(60));
}

function observeToolResult(result) {
  console.log(`\n${"─".repeat(60)}`);
  console.log("[TOOL RESULT]");
  console.log(typeof result === "string" ? result : JSON.stringify(result, null, 2));
  console.log("─".repeat(60));
}

function observeMemory(memoryDict) {
  console.log(`\n${"─".repeat(60)}`);
  console.log("[WORKING MEMORY STATE]");
  for (const [key, value] of Object.entries(memoryDict)) {
    if (Array.isArray(value)) {
      console.log(`  ${key}: [${value.length} items]`);
      for (const item of value) {
        console.log(`    - ${item}`);
      }
    } else {
      console.log(`  ${key}: ${value}`);
    }
  }
  console.log("─".repeat(60));
}

// =============================================================================
// TOOL DEFINITIONS
// =============================================================================

const TOOLS = [
  {
    name: "search_ucc_filings",
    description:
      "Search UCC filings by debtor name, state, status, or filing type. Returns matching filings.",
    input_schema: {
      type: "object",
      properties: {
        debtor_name: {
          type: "string",
          description: "Debtor name to search for (partial match, case-insensitive)",
        },
        state: {
          type: "string",
          description: "State to filter by, e.g. 'New York', 'California'",
        },
        status: {
          type: "string",
          description: "Filing status: 'Active', 'Terminated', 'Lapsed', 'Amendment'",
        },
      },
      required: [],
    },
  },
  {
    name: "get_filing_details",
    description:
      "Get full details of a specific UCC filing by its filing number.",
    input_schema: {
      type: "object",
      properties: {
        filing_number: {
          type: "string",
          description: "The UCC filing number, e.g. 'UCC-2024-NY-0012847'",
        },
      },
      required: ["filing_number"],
    },
  },
  {
    name: "update_working_memory",
    description:
      "Update the agent's working memory with new information. Use this after every tool call to track research state.",
    input_schema: {
      type: "object",
      properties: {
        key: {
          type: "string",
          description:
            "Memory key, e.g. 'current_debtor', 'findings_so_far', 'search_history'",
        },
        value: {
          type: "string",
          description:
            "Value to store (will be appended if key is 'findings_so_far' or 'search_history')",
        },
      },
      required: ["key", "value"],
    },
  },
];

// =============================================================================
// WORKING MEMORY CLASS — SOLUTION
// =============================================================================

class WorkingMemory {
  constructor() {
    this._store = {};
  }

  set(key, value) {
    this._store[key] = value;
  }

  get(key, defaultValue = undefined) {
    return key in this._store ? this._store[key] : defaultValue;
  }

  delete(key) {
    if (key in this._store) {
      delete this._store[key];
      return true;
    }
    return false;
  }

  clear() {
    this._store = {};
  }

  getContext() {
    const keys = Object.keys(this._store);
    if (keys.length === 0) {
      return "## Current Working Memory\nNo active research state.";
    }
    const lines = ["## Current Working Memory"];
    for (const [key, value] of Object.entries(this._store)) {
      if (Array.isArray(value)) {
        lines.push(`- ${key}:`);
        value.forEach((item, i) => lines.push(`  ${i + 1}. ${item}`));
      } else {
        lines.push(`- ${key}: ${value}`);
      }
    }
    return lines.join("\n");
  }

  toDict() {
    return { ...this._store };
  }

  static fromDict(data) {
    const mem = new WorkingMemory();
    mem._store = { ...data };
    return mem;
  }
}

// =============================================================================
// TOOL EXECUTION
// =============================================================================

function executeTool(toolName, toolInput, memory) {
  try {
    if (toolName === "search_ucc_filings") {
      const results = searchFilings({
        debtorName: toolInput.debtor_name,
        state: toolInput.state,
        status: toolInput.status,
        filingType: toolInput.filing_type,
      });
      return JSON.stringify(
        results.map((f) => ({
          filing_number: f.filing_number,
          debtor: f.debtor.name,
          secured_party: f.secured_party.name,
          state: f.state,
          status: f.status,
          collateral: f.collateral_description.substring(0, 100) + "...",
        })),
        null,
        2
      );
    } else if (toolName === "get_filing_details") {
      const filing = getFilingByNumber(toolInput.filing_number);
      if (filing) return JSON.stringify(filing, null, 2);
      return JSON.stringify({
        error: `Filing ${toolInput.filing_number} not found`,
      });
    } else if (toolName === "update_working_memory") {
      const { key, value } = toolInput;
      if (key === "findings_so_far" || key === "search_history") {
        let existing = memory.get(key, []);
        if (!Array.isArray(existing)) existing = [existing];
        existing.push(value);
        memory.set(key, existing);
      } else {
        memory.set(key, value);
      }
      return JSON.stringify({ status: "ok", key, value: memory.get(key) });
    } else {
      return JSON.stringify({ error: `Unknown tool: ${toolName}` });
    }
  } catch (e) {
    return JSON.stringify({ error: `Tool execution failed: ${e.message}` });
  }
}

// =============================================================================
// AGENT WITH WORKING MEMORY — SOLUTION
// =============================================================================

async function runResearchAgent(userMessage, memory, maxTurns = 10) {
  observe("QUERY", userMessage);

  // Build system prompt with working memory context
  const memoryContext = memory.getContext();
  const systemPrompt = `You are a UCC (Uniform Commercial Code) filing research agent. You help users
research UCC filings, track liens, and assess debtor risk.

You have a working memory scratchpad to track your research state. ALWAYS use
the update_working_memory tool to record:
- current_debtor: the name of the entity you are researching
- findings_so_far: each significant finding (appended as a list)
- search_history: each search you perform (appended as a list)

Update working memory AFTER each search or discovery. This ensures you can
resume research across conversation turns.

${memoryContext}`;

  const messages = [{ role: "user", content: userMessage }];

  // Agent loop
  for (let turn = 0; turn < maxTurns; turn++) {
    const response = await client.messages.create({
      model: MODEL,
      max_tokens: 4096,
      system: systemPrompt,
      tools: TOOLS,
      messages,
    });

    // If Claude is done, extract text and return
    if (response.stop_reason !== "tool_use") {
      let finalText = "";
      for (const block of response.content) {
        if (block.type === "text") finalText += block.text;
      }
      observe(
        "RESPONSE",
        finalText.length > 200
          ? finalText.substring(0, 200) + "..."
          : finalText
      );
      return finalText;
    }

    // Process tool calls
    const toolResults = [];
    for (const block of response.content) {
      if (block.type === "tool_use") {
        observeToolCall(block.name, block.input);
        const result = executeTool(block.name, block.input, memory);
        observeToolResult(result);
        toolResults.push({
          type: "tool_result",
          tool_use_id: block.id,
          content: result,
        });
      }
    }

    // Append assistant message and tool results
    messages.push({ role: "assistant", content: response.content });
    messages.push({ role: "user", content: toolResults });

    // Log current memory state
    observeMemory(memory.toDict());
  }

  return "Agent did not produce a final response within max turns.";
}

// =============================================================================
// MAIN
// =============================================================================

console.log("=".repeat(60));
console.log("M11 Lab - Step 1: Working Memory Scratchpad (SOLUTION)");
console.log("=".repeat(60));

const memory = new WorkingMemory();

// Turn 1: Start researching a debtor
console.log("\n\n>>> Turn 1: Start research");
const result1 = await runResearchAgent(
  "Research Greenfield Logistics LLC. Find all their UCC filings and tell me about any liens.",
  memory
);
console.log(`\nFINAL ANSWER: ${result1}`);

// Show memory state after turn 1
console.log("\n\n>>> Working Memory after Turn 1:");
observeMemory(memory.toDict());

// Turn 2: Continue research (memory carries forward)
console.log("\n\n>>> Turn 2: Follow-up question (memory carries forward)");
const result2 = await runResearchAgent(
  "What secured parties are involved with this debtor? Are there any blanket liens?",
  memory
);
console.log(`\nFINAL ANSWER: ${result2}`);

// Show final memory state
console.log("\n\n>>> Working Memory after Turn 2:");
observeMemory(memory.toDict());

// Demonstrate persistence
console.log("\n\n>>> Persistence Test: Serialize and restore");
const saved = JSON.stringify(memory.toDict(), null, 2);
console.log(`Saved memory: ${saved}`);
const restoredMemory = WorkingMemory.fromDict(JSON.parse(saved));
console.log(`Restored memory context:\n${restoredMemory.getContext()}`);
