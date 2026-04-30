/**
 * M11 Lab - Step 2: Episodic Memory with Vector Search (Solution)
 * ==============================================================
 * Complete solution: episodic memory backed by ChromaDB for storing
 * and recalling past conversation summaries via semantic search.
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
// MOCK EPISODES
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
// EPISODIC MEMORY CLASS — SOLUTION
// =============================================================================

class EpisodicMemory {
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
    const episodeId = `episode_${this._episodeCount}`;
    this._episodeCount++;

    if (!metadata.timestamp) {
      metadata.timestamp = new Date().toISOString();
    }

    // ChromaDB metadata values must be str, int, float, or bool
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
          similarity: results.distances ? 1 - results.distances[0][i] : 0,
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
// TOOL DEFINITIONS
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
// TOOL EXECUTION
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
// AGENT WITH EPISODIC MEMORY — SOLUTION
// =============================================================================

async function runEpisodicAgent(userMessage, episodic, maxTurns = 10) {
  observe("QUERY", userMessage);

  const systemPrompt = `You are a UCC (Uniform Commercial Code) filing research agent with episodic memory.
You can recall similar past research sessions to inform your current work.

IMPORTANT WORKFLOW:
1. ALWAYS call recall_similar_research FIRST before doing any new research.
   This checks if you have relevant prior experience with this debtor or topic.
2. If past research is found, reference it in your response and note what's new vs. already known.
3. Then proceed with any additional searches needed.
4. Provide a comprehensive summary that integrates both past and current findings.`;

  const messages = [{ role: "user", content: userMessage }];

  for (let turn = 0; turn < maxTurns; turn++) {
    const response = await client.messages.create({
      model: MODEL,
      max_tokens: 4096,
      system: systemPrompt,
      tools: TOOLS,
      messages,
    });

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

    const toolResults = [];
    for (const block of response.content) {
      if (block.type === "tool_use") {
        observeToolCall(block.name, block.input);
        const result = await executeTool(block.name, block.input, episodic);
        observeToolResult(result);
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

  return "Agent did not produce a final response within max turns.";
}

// =============================================================================
// MAIN
// =============================================================================

console.log("=".repeat(60));
console.log("M11 Lab - Step 2: Episodic Memory with Vector Search (SOLUTION)");
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
