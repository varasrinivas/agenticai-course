/**
 * M11 Lab - Step 2: Episodic Memory with Vector Search (Starter)
 * ==============================================================
 * Build an episodic memory backed by ChromaDB that stores past
 * conversation summaries and retrieves similar experiences when
 * the agent encounters a related query.
 *
 * KEY CONCEPT: Episodic memory lets your agent say "I've seen
 * something like this before." It stores summaries of past research
 * sessions as vectors and retrieves the most relevant ones when a
 * new query arrives — giving the agent long-term learning capability.
 *
 * Usage:
 *     node episodic_memory.js
 */

import Anthropic from "@anthropic-ai/sdk";
import "dotenv/config";
import { ChromaClient } from "chromadb";
import { searchFilings, getFilingByNumber } from "../../shared/mock_ucc_data.js";

const client = new Anthropic();
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

function observeEpisodes(episodes) {
  console.log(`\n${"─".repeat(60)}`);
  console.log(`[EPISODIC MEMORY RECALL] Found ${episodes.length} similar episodes`);
  for (let i = 0; i < episodes.length; i++) {
    const ep = episodes[i];
    const score = ep.similarity !== undefined ? ep.similarity.toFixed(3) : "N/A";
    console.log(`  ${i + 1}. [score=${score}] ${ep.summary}`);
    if (ep.metadata) {
      console.log(`     metadata: ${JSON.stringify(ep.metadata)}`);
    }
  }
  console.log("─".repeat(60));
}

// =============================================================================
// MOCK EPISODES (complete -- do not modify)
// =============================================================================

const MOCK_EPISODES = [
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

// =============================================================================
// EPISODIC MEMORY CLASS — YOUR CODE HERE
// =============================================================================

class EpisodicMemory {
  /**
   * Vector-backed episodic memory using ChromaDB.
   *
   * Stores conversation summaries as embeddings and retrieves
   * similar past experiences via semantic search.
   */

  constructor() {
    this._client = null;
    this._collection = null;
    this._episodeCount = 0;
  }

  async init(collectionName = "ucc_episodes") {
    this._client = new ChromaClient();
    this._collection = await this._client.getOrCreateCollection({
      name: collectionName,
      metadata: { "hnsw:space": "cosine" },
    });
  }

  async storeEpisode(summary, metadata = {}) {
    /**
     * Store a conversation summary as an episode in ChromaDB.
     *
     * Args:
     *     summary: Text summary of the conversation/research session
     *     metadata: Optional object with keys like debtor, state, risk_level, timestamp
     *
     * Returns:
     *     The episode ID
     */
    // ------------------------------------------------------------------
    // TODO 1: Implement storeEpisode()
    //   - Generate a unique episode ID (e.g., `episode_${this._episodeCount}`)
    //   - Increment this._episodeCount
    //   - Add a timestamp to metadata if not present
    //   - Use this._collection.add() with:
    //     documents: [summary]
    //     metadatas: [metadata] (ensure all values are strings for ChromaDB)
    //     ids: [episodeId]
    //   - Return the episode ID
    //
    // GOTCHA: ChromaDB metadata values must be str, int, float, or bool.
    //   Convert any other types to strings.
    // ------------------------------------------------------------------
    return "";
  }

  async recall(query, nResults = 3) {
    /**
     * Find similar past episodes via semantic search.
     *
     * Args:
     *     query: The search query (natural language)
     *     nResults: Number of results to return
     *
     * Returns:
     *     Array of objects with keys: summary, metadata, similarity
     */
    // ------------------------------------------------------------------
    // TODO 2: Implement recall()
    //   - Use this._collection.query() with queryTexts: [query], nResults
    //   - Handle the case where the collection is empty (return [])
    //   - Transform the ChromaDB result into an array of objects:
    //     [{ summary: doc, metadata: meta, similarity: 1 - distance }, ...]
    //   - ChromaDB returns distances (lower = more similar for cosine)
    //     so similarity = 1 - distance
    //   - Return the array sorted by similarity (highest first)
    // ------------------------------------------------------------------
    return [];
  }

  async getRecent(n = 5) {
    /**
     * Get the N most recent episodes.
     *
     * Returns:
     *     Array of objects with keys: summary, metadata
     */
    // ------------------------------------------------------------------
    // TODO 3: Implement getRecent()
    //   - Use this._collection.get() to retrieve all episodes
    //   - Sort by timestamp in metadata (most recent first)
    //   - Return the top N as array of objects: [{ summary, metadata }, ...]
    //   - Handle empty collection gracefully
    // ------------------------------------------------------------------
    return [];
  }

  async populateMockEpisodes() {
    console.log("[EPISODIC MEMORY] Loading mock episodes...");
    for (const ep of MOCK_EPISODES) {
      const episodeId = await this.storeEpisode(ep.summary, ep.metadata);
      console.log(
        `  Stored: ${episodeId} — ${ep.summary.substring(0, 60)}...`
      );
    }
    console.log(
      `[EPISODIC MEMORY] ${MOCK_EPISODES.length} episodes loaded.\n`
    );
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
      "Search episodic memory for similar past research sessions. Use this FIRST before doing new research to see if we have relevant prior experience.",
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
];

// =============================================================================
// TOOL EXECUTION (complete -- do not modify)
// =============================================================================

async function executeTool(toolName, toolInput, episodic) {
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
      const episodes = await episodic.recall(toolInput.query, 3);
      if (episodes.length > 0) {
        observeEpisodes(episodes);
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
    } else {
      return JSON.stringify({ error: `Unknown tool: ${toolName}` });
    }
  } catch (e) {
    return JSON.stringify({ error: `Tool execution failed: ${e.message}` });
  }
}

// =============================================================================
// AGENT WITH EPISODIC MEMORY — YOUR CODE HERE
// =============================================================================

async function runEpisodicAgent(userMessage, episodic, maxTurns = 10) {
  /**
   * Run a research agent that uses episodic memory to recall similar past research.
   *
   * The agent:
   * 1. First checks episodic memory for similar past research
   * 2. Uses that context to inform current research
   * 3. Runs UCC filing searches as needed
   * 4. Returns findings with context from past sessions
   *
   * Returns Claude's final text response.
   */
  observe("QUERY", userMessage);

  // ------------------------------------------------------------------
  // TODO 4: Build the system prompt
  //   - Instruct Claude that it is a UCC research agent with episodic memory
  //   - Tell it to ALWAYS call recall_similar_research first before
  //     doing new research, to check for relevant past experience
  //   - Tell it to reference past research in its response when relevant
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
  //     b) Execute with executeTool (pass episodic memory)
  //     c) Log with observeToolResult
  //   - Append assistant response and tool results to messages
  // ------------------------------------------------------------------

  return "Agent did not produce a final response within max turns.";
}

// =============================================================================
// MAIN
// =============================================================================

console.log("=".repeat(60));
console.log("M11 Lab - Step 2: Episodic Memory with Vector Search");
console.log("=".repeat(60));

const episodic = new EpisodicMemory();
await episodic.init();
await episodic.populateMockEpisodes();

// Test 1: Query about a debtor we've researched before
console.log("\n\n>>> Test 1: Query about a previously researched debtor");
const result1 = await runEpisodicAgent(
  "I need to research Greenfield Logistics. What do we know?",
  episodic
);
console.log(`\nFINAL ANSWER: ${result1}`);

// Test 2: Query about a debtor with similar characteristics
console.log(
  "\n\n>>> Test 2: Query about a new debtor (should find similar past research)"
);
const result2 = await runEpisodicAgent(
  "Research a company called Midwest Agricultural Cooperative. Are there any equipment liens?",
  episodic
);
console.log(`\nFINAL ANSWER: ${result2}`);

// Test 3: Store a new episode and recall it
console.log("\n\n>>> Test 3: Store new episode and verify recall");
await episodic.storeEpisode(
  "Researched Midwest Agricultural Cooperative — found active filing in IL, farm products collateral including crops and livestock, secured by Farm Credit Services.",
  {
    debtor: "Midwest Agricultural Cooperative",
    state: "Illinois",
    risk_level: "medium",
    timestamp: "2024-10-01T10:00:00Z",
  }
);
const result3 = await runEpisodicAgent(
  "What do we know about agricultural companies in our research history?",
  episodic
);
console.log(`\nFINAL ANSWER: ${result3}`);

// Show recent episodes
console.log("\n\n>>> Recent Episodes:");
const recent = await episodic.getRecent(3);
for (let i = 0; i < recent.length; i++) {
  console.log(`  ${i + 1}. ${recent[i].summary.substring(0, 80)}...`);
  console.log(`     ${JSON.stringify(recent[i].metadata || {})}`);
}
