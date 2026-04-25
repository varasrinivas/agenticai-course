/**
 * M11 Lab - Step 1: Working Memory Scratchpad (Starter)
 * =====================================================
 * Build a key-value working memory that an agent uses to track
 * current task state across tool calls and conversation turns.
 *
 * KEY CONCEPT: Working memory is the agent's "scratchpad" — it holds
 * the current debtor being researched, findings so far, and search
 * history. This context is injected into every system prompt so Claude
 * always knows where it left off.
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
// TOOL DEFINITIONS (complete -- do not modify)
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
// WORKING MEMORY CLASS — YOUR CODE HERE
// =============================================================================

class WorkingMemory {
  /**
   * A key-value scratchpad for tracking current task state.
   *
   * The agent uses this to remember:
   * - current_debtor: who we are researching
   * - findings_so_far: list of discoveries made during research
   * - search_history: list of searches performed
   */

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
    /**
     * Format all working memory entries into a string suitable for
     * injection into the system prompt.
     *
     * Returns a string like:
     *     ## Current Working Memory
     *     - current_debtor: Greenfield Logistics LLC
     *     - findings_so_far:
     *       1. Found active filing in NY
     *       2. Blanket lien by Atlantic Capital
     *     - search_history:
     *       1. Searched by debtor name 'Greenfield'
     */
    // ------------------------------------------------------------------
    // TODO 1: Implement getContext()
    //   - If memory is empty, return "## Current Working Memory\nNo active research state."
    //   - Otherwise, build a formatted string with all key-value pairs
    //   - For array values, number each item
    //   - For string/other values, display directly
    // ------------------------------------------------------------------
    return "";
  }

  toDict() {
    /**
     * Serialize working memory to a plain object for JSON persistence.
     */
    // ------------------------------------------------------------------
    // TODO 2: Implement toDict()
    //   - Return a deep copy of the internal store
    //   - This should be JSON-serializable
    // ------------------------------------------------------------------
    return {};
  }

  static fromDict(data) {
    /**
     * Deserialize working memory from a plain object.
     */
    // ------------------------------------------------------------------
    // TODO 3: Implement fromDict()
    //   - Create a new WorkingMemory instance
    //   - Populate its _store with the provided data
    //   - Return the instance
    // ------------------------------------------------------------------
    return new WorkingMemory();
  }
}

// =============================================================================
// TOOL EXECUTION (complete -- do not modify)
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
      if (filing) {
        return JSON.stringify(filing, null, 2);
      }
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
// AGENT WITH WORKING MEMORY — YOUR CODE HERE
// =============================================================================

async function runResearchAgent(userMessage, memory, maxTurns = 10) {
  /**
   * Run a research agent that uses working memory to track state.
   *
   * The agent:
   * 1. Gets the current working memory context
   * 2. Includes it in the system prompt
   * 3. Runs the tool loop
   * 4. Updates working memory after each tool call
   * 5. Returns the final response
   *
   * Returns Claude's final text response.
   */
  observe("QUERY", userMessage);

  // ------------------------------------------------------------------
  // TODO 4: Build the system prompt with working memory context
  //   - Start with a base system prompt explaining the agent's role
  //   - Call memory.getContext() and append it to the system prompt
  //   - The system prompt should instruct Claude to:
  //     a) Research UCC filings as requested
  //     b) Use update_working_memory after each search/finding
  //     c) Track current_debtor, findings_so_far, search_history
  // ------------------------------------------------------------------
  const systemPrompt = ""; // Replace with your system prompt

  const messages = [{ role: "user", content: userMessage }];

  // ------------------------------------------------------------------
  // TODO 5: Implement the agent loop
  //   - Loop up to maxTurns
  //   - Call client.messages.create with model, max_tokens, system, tools, messages
  //   - If stop_reason !== "tool_use", extract text and return
  //   - Otherwise, process each tool_use block:
  //     a) Log with observeToolCall
  //     b) Execute with executeTool
  //     c) Log with observeToolResult
  //   - Append assistant response and tool results to messages
  //   - After each loop iteration, log memory state with observeMemory
  // ------------------------------------------------------------------

  return "Agent did not produce a final response within max turns.";
}

// =============================================================================
// MAIN
// =============================================================================

console.log("=".repeat(60));
console.log("M11 Lab - Step 1: Working Memory Scratchpad");
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
