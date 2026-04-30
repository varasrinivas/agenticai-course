/**
 * M11 Lab - Step 3: Full 3-Tier Memory Agent (Starter)
 * ====================================================
 * Combine working memory, episodic memory, and procedural memory
 * into a single agent that orchestrates all three tiers during
 * UCC research sessions.
 *
 * KEY CONCEPT: A production agent needs all three memory tiers
 * working together. Procedural memory tells it HOW to research
 * (learned patterns). Episodic memory tells it WHAT it has seen
 * before (past experience). Working memory tracks WHERE it is
 * right now (current state). The orchestration layer decides
 * which tier to consult at each step.
 *
 * Usage:
 *     node memory_agent.js
 */

import Anthropic from "@anthropic-ai/sdk";
import "dotenv/config";
import { ChromaClient } from "chromadb";
import { searchFilings, getFilingByNumber } from "../../shared/mock_ucc_data.js";

const anthropicClient = new Anthropic();
const MODEL = "claude-sonnet-4-6";

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

function observeMemory(label, data) {
  console.log(`\n${"─".repeat(60)}`);
  console.log(`[${label}]`);
  if (typeof data === "object" && data !== null) {
    for (const [key, value] of Object.entries(data)) {
      if (Array.isArray(value)) {
        console.log(`  ${key}: [${value.length} items]`);
        for (const item of value) {
          console.log(`    - ${typeof item === "string" ? item : JSON.stringify(item)}`);
        }
      } else {
        console.log(`  ${key}: ${value}`);
      }
    }
  } else {
    console.log(`  ${data}`);
  }
  console.log("─".repeat(60));
}

// =============================================================================
// PROCEDURAL MEMORY (complete -- do not modify)
// =============================================================================

const PROCEDURAL_MEMORY = {
  entity_search: {
    description: "Standard entity research workflow",
    steps: [
      "search by debtor name",
      "get filing details",
      "check for amendments",
      "assess risk",
    ],
    triggers: ["research", "investigate", "look up", "find", "search for"],
  },
  risk_assessment: {
    description: "Lien risk evaluation pattern",
    steps: [
      "count active filings",
      "check for blanket liens",
      "check expiration dates",
      "flag multiple secured parties",
    ],
    triggers: ["risk", "assess", "evaluate", "how risky", "lien risk"],
  },
  amendment_tracking: {
    description: "Track changes to UCC filings over time",
    steps: [
      "find original filing",
      "search for UCC-3 amendments",
      "compare collateral descriptions",
      "build timeline",
    ],
    triggers: ["amendment", "changed", "modified", "updated", "history"],
  },
  multi_state_search: {
    description: "Search across multiple states for related filings",
    steps: [
      "search debtor in primary state",
      "check state of incorporation",
      "search in Delaware (common incorporation state)",
      "search in other likely states",
      "consolidate findings",
    ],
    triggers: [
      "multi-state",
      "all states",
      "everywhere",
      "nationwide",
      "cross-state",
    ],
  },
};

// =============================================================================
// WORKING MEMORY CLASS (complete -- from Step 1)
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
// EPISODIC MEMORY CLASS (complete -- from Step 2)
// =============================================================================

class EpisodicMemory {
  constructor() {
    this._client = null;
    this._collection = null;
    this._episodeCount = 0;
  }

  async init(collectionName = "ucc_agent_episodes") {
    this._client = new ChromaClient();
    this._collection = await this._client.getOrCreateCollection({
      name: collectionName,
      metadata: { "hnsw:space": "cosine" },
    });
  }

  async storeEpisode(summary, metadata = {}) {
    const episodeId = `episode_${this._episodeCount}`;
    this._episodeCount++;
    if (!metadata.timestamp) {
      metadata.timestamp = new Date().toISOString();
    }
    const cleanMeta = {};
    for (const [k, v] of Object.entries(metadata)) {
      cleanMeta[k] =
        typeof v === "string" ||
        typeof v === "number" ||
        typeof v === "boolean"
          ? v
          : String(v);
    }
    await this._collection.add({
      documents: [summary],
      metadatas: [cleanMeta],
      ids: [episodeId],
    });
    return episodeId;
  }

  async recall(query, nResults = 3) {
    try {
      const count = await this._collection.count();
      if (count === 0) return [];
      const n = Math.min(nResults, count);
      const results = await this._collection.query({
        queryTexts: [query],
        nResults: n,
      });
      const episodes = [];
      for (let i = 0; i < results.documents[0].length; i++) {
        episodes.push({
          summary: results.documents[0][i],
          metadata: results.metadatas ? results.metadatas[0][i] : {},
          similarity: results.distances
            ? 1 - results.distances[0][i]
            : 0,
        });
      }
      return episodes.sort((a, b) => b.similarity - a.similarity);
    } catch {
      return [];
    }
  }

  async getRecent(n = 5) {
    try {
      const allData = await this._collection.get();
      if (!allData.documents || allData.documents.length === 0) return [];
      const episodes = allData.documents.map((doc, i) => ({
        summary: doc,
        metadata: allData.metadatas ? allData.metadatas[i] : {},
      }));
      episodes.sort(
        (a, b) =>
          (b.metadata?.timestamp || "").localeCompare(
            a.metadata?.timestamp || ""
          )
      );
      return episodes.slice(0, n);
    } catch {
      return [];
    }
  }

  async populateMockEpisodes() {
    const mock = [
      {
        summary:
          "Researched Greenfield Logistics — found active filing in NY, blanket lien by Atlantic Capital Partners covering all accounts receivable, inventory, equipment, and general intangibles.",
        metadata: {
          debtor: "Greenfield Logistics LLC",
          state: "New York",
          risk_level: "high",
          timestamp: "2024-08-15T10:30:00Z",
        },
      },
      {
        summary:
          "Investigated Pacific Ridge Technologies — DE incorporation but CA filing, extensive IP collateral including patents and trademarks, secured by Silicon Valley Bank.",
        metadata: {
          debtor: "Pacific Ridge Technologies Inc",
          state: "California",
          risk_level: "medium",
          timestamp: "2024-08-20T14:15:00Z",
        },
      },
      {
        summary:
          "Searched for Lone Star Energy — found equipment-specific lien on Caterpillar excavators and Liebherr crane, secured by Wells Fargo Equipment Finance in Texas.",
        metadata: {
          debtor: "Lone Star Energy Solutions LP",
          state: "Texas",
          risk_level: "low",
          timestamp: "2024-09-02T09:00:00Z",
        },
      },
      {
        summary:
          "Looked into Sunshine Medical Group — found UCC-3 amendment adding MRI equipment and CT scanner to existing lien, TD Bank is secured party in Florida.",
        metadata: {
          debtor: "Sunshine Medical Group PA",
          state: "Florida",
          risk_level: "medium",
          timestamp: "2024-09-10T11:45:00Z",
        },
      },
      {
        summary:
          "Checked Nextera Holdings — massive blanket lien by JPMorgan Chase covering all assets including commercial tort claims, minerals, and investment property in Delaware.",
        metadata: {
          debtor: "Nextera Holdings Corp",
          state: "Delaware",
          risk_level: "critical",
          timestamp: "2024-09-15T16:20:00Z",
        },
      },
    ];
    console.log("[EPISODIC MEMORY] Loading mock episodes...");
    for (const ep of mock) {
      const eid = await this.storeEpisode(ep.summary, ep.metadata);
      console.log(`  Stored: ${eid} — ${ep.summary.substring(0, 60)}...`);
    }
    console.log(`[EPISODIC MEMORY] ${mock.length} episodes loaded.\n`);
  }
}

// =============================================================================
// TOOL DEFINITIONS (complete -- do not modify)
// =============================================================================

const TOOLS = [
  {
    name: "search_ucc_filings",
    description:
      "Search UCC filings by debtor name, state, status, or filing type.",
    input_schema: {
      type: "object",
      properties: {
        debtor_name: {
          type: "string",
          description: "Debtor name to search for",
        },
        state: { type: "string", description: "State to filter by" },
        status: { type: "string", description: "Filing status filter" },
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
          description: "The UCC filing number",
        },
      },
      required: ["filing_number"],
    },
  },
  {
    name: "recall_similar_research",
    description:
      "Search episodic memory for similar past research sessions.",
    input_schema: {
      type: "object",
      properties: {
        query: {
          type: "string",
          description: "What to search for in past research sessions",
        },
      },
      required: ["query"],
    },
  },
  {
    name: "update_working_memory",
    description: "Update the agent's working memory with new information.",
    input_schema: {
      type: "object",
      properties: {
        key: { type: "string", description: "Memory key" },
        value: { type: "string", description: "Value to store" },
      },
      required: ["key", "value"],
    },
  },
  {
    name: "get_procedural_pattern",
    description:
      "Look up a procedural memory pattern for a given task type. Returns the step-by-step workflow.",
    input_schema: {
      type: "object",
      properties: {
        task_description: {
          type: "string",
          description: "Description of the task to find a pattern for",
        },
      },
      required: ["task_description"],
    },
  },
];

// =============================================================================
// TOOL EXECUTION (complete -- do not modify)
// =============================================================================

async function executeTool(toolName, toolInput, agent) {
  try {
    if (toolName === "search_ucc_filings") {
      const results = searchFilings({
        debtorName: toolInput.debtor_name,
        state: toolInput.state,
        status: toolInput.status,
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
    } else if (toolName === "recall_similar_research") {
      const episodes = await agent.episodicMemory.recall(
        toolInput.query,
        3
      );
      if (episodes.length > 0) {
        return JSON.stringify(
          episodes.map((ep) => ({
            summary: ep.summary,
            similarity: Math.round((ep.similarity || 0) * 1000) / 1000,
            metadata: ep.metadata || {},
          })),
          null,
          2
        );
      }
      return JSON.stringify({ message: "No similar past research found." });
    } else if (toolName === "update_working_memory") {
      const { key, value } = toolInput;
      if (key === "findings_so_far" || key === "search_history") {
        let existing = agent.workingMemory.get(key, []);
        if (!Array.isArray(existing)) existing = [existing];
        existing.push(value);
        agent.workingMemory.set(key, existing);
      } else {
        agent.workingMemory.set(key, value);
      }
      return JSON.stringify({
        status: "ok",
        key,
        value: agent.workingMemory.get(key),
      });
    } else if (toolName === "get_procedural_pattern") {
      const task = toolInput.task_description.toLowerCase();
      const matched = [];
      for (const [patternName, pattern] of Object.entries(
        PROCEDURAL_MEMORY
      )) {
        for (const trigger of pattern.triggers) {
          if (task.includes(trigger)) {
            matched.push({
              pattern: patternName,
              description: pattern.description,
              steps: pattern.steps,
            });
            break;
          }
        }
      }
      if (matched.length > 0) {
        observeMemory("PROCEDURAL MEMORY MATCH", { patterns: matched });
        return JSON.stringify(matched, null, 2);
      }
      return JSON.stringify({
        message: "No matching procedural pattern found.",
        available_patterns: Object.keys(PROCEDURAL_MEMORY),
      });
    } else {
      return JSON.stringify({ error: `Unknown tool: ${toolName}` });
    }
  } catch (e) {
    return JSON.stringify({ error: `Tool execution failed: ${e.message}` });
  }
}

// =============================================================================
// MEMORY AGENT CLASS — YOUR CODE HERE
// =============================================================================

class MemoryAgent {
  /**
   * A 3-tier memory agent that combines:
   * - Working memory: current task state (key-value scratchpad)
   * - Episodic memory: past research sessions (vector DB)
   * - Procedural memory: learned research patterns (JSON)
   */

  constructor() {
    this.workingMemory = new WorkingMemory();
    this.episodicMemory = new EpisodicMemory();
    this.proceduralMemory = PROCEDURAL_MEMORY;
  }

  async initialize() {
    await this.episodicMemory.init();
    await this.episodicMemory.populateMockEpisodes();
  }

  getSystemPrompt() {
    /**
     * Build the full system prompt incorporating all three memory tiers.
     *
     * Returns a system prompt that includes:
     * 1. Agent role and capabilities
     * 2. Current working memory state
     * 3. Available procedural patterns
     * 4. Instructions to use episodic memory via recall tool
     */
    // ------------------------------------------------------------------
    // TODO 1: Build the system prompt
    //   - Start with the agent's role description
    //   - Include this.workingMemory.getContext()
    //   - Include a summary of available procedural patterns
    //   - Instruct the agent to:
    //     a) FIRST check for a procedural pattern matching the task
    //     b) THEN recall similar past research from episodic memory
    //     c) Use working memory to track state throughout
    //     d) Follow the procedural pattern steps if one matches
    // ------------------------------------------------------------------
    return "";
  }

  async run(userMessage, maxTurns = 15) {
    /**
     * Run a research session using all 3 memory tiers.
     *
     * Returns Claude's final text response.
     */
    observe("QUERY", userMessage);

    // ------------------------------------------------------------------
    // TODO 2: Implement the agent run method
    //   - Get the system prompt from this.getSystemPrompt()
    //   - Create the messages array with the user message
    //   - Run the agent loop (up to maxTurns):
    //     a) Call anthropicClient.messages.create
    //     b) If stop_reason !== "tool_use", extract text and break
    //     c) Process tool_use blocks, execute tools, collect results
    //     d) Append to messages
    //     e) Log memory state after each iteration
    //   - Return the final text response
    // ------------------------------------------------------------------
    return "Agent did not produce a final response within max turns.";
  }

  async storeSessionAsEpisode(userQuery, finalResponse) {
    /**
     * After a research session completes, store it as a new episodic memory.
     */
    // ------------------------------------------------------------------
    // TODO 3: Implement storeSessionAsEpisode()
    //   - Build a summary from the user query and key findings
    //   - Include relevant metadata from working memory
    //   - Call this.episodicMemory.storeEpisode()
    //   - Return the episode ID
    // ------------------------------------------------------------------
    return "";
  }
}

// =============================================================================
// MAIN
// =============================================================================

console.log("=".repeat(60));
console.log("M11 Lab - Step 3: Full 3-Tier Memory Agent");
console.log("=".repeat(60));

const agent = new MemoryAgent();
await agent.initialize();

// Session 1: Research a debtor
console.log("\n\n>>> Session 1: Research Greenfield Logistics");
const result1 = await agent.run(
  "Research Greenfield Logistics LLC and assess their lien risk."
);
console.log(`\nFINAL ANSWER: ${result1}`);

// Store session 1 as an episode
console.log("\n\n>>> Storing Session 1 as episode...");
const episodeId = await agent.storeSessionAsEpisode(
  "Research Greenfield Logistics LLC and assess their lien risk.",
  result1
);
console.log(`Stored as: ${episodeId}`);

// Show all memory states
console.log("\n\n>>> Memory State After Session 1:");
observeMemory("WORKING MEMORY", agent.workingMemory.toDict());
observeMemory(
  "PROCEDURAL MEMORY",
  Object.fromEntries(
    Object.entries(agent.proceduralMemory).map(([k, v]) => [
      k,
      v.description,
    ])
  )
);
const recent = await agent.episodicMemory.getRecent(3);
observeMemory(
  "EPISODIC MEMORY (recent)",
  Object.fromEntries(
    recent.map((ep, i) => [
      `episode_${i + 1}`,
      ep.summary.substring(0, 80) + "...",
    ])
  )
);

// Clear working memory for session 2
agent.workingMemory.clear();

// Session 2: Research another debtor (should recall session 1)
console.log(
  "\n\n>>> Session 2: Research Peachtree Ventures (should recall past sessions)"
);
const result2 = await agent.run(
  "Research Peachtree Ventures LLC. I need to evaluate their lien risk and compare to other companies we've researched."
);
console.log(`\nFINAL ANSWER: ${result2}`);

// Store session 2
const episodeId2 = await agent.storeSessionAsEpisode(
  "Research Peachtree Ventures LLC lien risk",
  result2
);
console.log(`\nStored as: ${episodeId2}`);

// Final memory summary
console.log("\n\n>>> Final Memory Summary:");
observeMemory("WORKING MEMORY", agent.workingMemory.toDict());
const allRecent = await agent.episodicMemory.getRecent(5);
console.log(`\n[EPISODIC MEMORY] Total episodes: ${allRecent.length}`);
for (let i = 0; i < allRecent.length; i++) {
  console.log(`  ${i + 1}. ${allRecent[i].summary.substring(0, 80)}...`);
}
