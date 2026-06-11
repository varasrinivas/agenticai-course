/**
 * M06 Lab - Step 1: Tools, Mocks, Dispatcher, Registry (COMPLETE)
 * ================================================================
 * Five research tools. Imported by research_agent.js.
 * Run standalone to sanity-check: node tools_registry.js
 */

import { pathToFileURL } from "node:url";

// ── Tool Schemas (OpenAI format) ──────────────────────────────
// NOTE how descriptions choreograph the chain: "Use after web_search",
// "Use after fetch_page" — the model learns the sequence from these.
export const TOOLS = [
  {
    type: "function",
    function: {
      name: "web_search",
      description:
        "Search the web for current information. Returns top 3 " +
        "results with title, URL, and snippet. Use for recent " +
        "events, factual questions, or general research.",
      parameters: {
        type: "object",
        properties: { query: { type: "string", description: "Search query" } },
        required: ["query"],
      },
    },
  },
  {
    type: "function",
    function: {
      name: "fetch_page",
      description:
        "Fetch the full text content of a web page by URL. " +
        "Returns page text (max 5000 chars). Use after " +
        "web_search to get full content from a result URL.",
      parameters: {
        type: "object",
        properties: { url: { type: "string", description: "Full URL to fetch" } },
        required: ["url"],
      },
    },
  },
  {
    type: "function",
    function: {
      name: "summarize_text",
      description:
        "Summarize long text into key points (3-5 bullets). " +
        "Use after fetch_page to condense page content.",
      parameters: {
        type: "object",
        properties: {
          text: { type: "string", description: "Text to summarize" },
          max_points: { type: "integer", description: "Max bullet points (default 5)" },
        },
        required: ["text"],
      },
    },
  },
  {
    type: "function",
    function: {
      name: "format_citation",
      description:
        "Format a source as an academic citation. Use after " +
        "summaries are ready to create proper references.",
      parameters: {
        type: "object",
        properties: {
          title: { type: "string", description: "Article title" },
          url: { type: "string", description: "Source URL" },
          accessed_date: { type: "string", description: "e.g. '2025-01-15'" },
        },
        required: ["title", "url"],
      },
    },
  },
  {
    type: "function",
    function: {
      name: "save_to_file",
      description: "Save content to a local file. Returns file path.",
      parameters: {
        type: "object",
        properties: {
          filename: { type: "string", description: "Output filename" },
          content: { type: "string", description: "Content to save" },
        },
        required: ["filename", "content"],
      },
    },
  },
];

// ── Mock Implementations (replace with real APIs in production) ──
async function webSearch(query) {
  await new Promise((r) => setTimeout(r, 200)); // simulated latency
  return { results: [
    { title: `Result 1: ${query}`, url: "https://example.com/1", snippet: `Overview of ${query}...` },
    { title: `Result 2: ${query}`, url: "https://example.com/2", snippet: `Developments in ${query}...` },
    { title: `Result 3: ${query}`, url: "https://broken.example.com/404", snippet: `Deep dive into ${query}...` },
  ]};
}

async function fetchPage(url) {
  await new Promise((r) => setTimeout(r, 300));
  if (url.includes("broken") || url.includes("404")) {
    throw new Error(`404 Not Found: ${url}`); // deliberate failure path
  }
  return { content: `Full page content from ${url}. `.repeat(20) };
}

function summarizeText(text, maxPoints = 5) {
  return { summary: Array.from({ length: Math.min(maxPoints, 5) }, (_, i) => `Key point ${i + 1}`) };
}

function formatCitation(title, url, accessedDate) {
  const date = accessedDate || "2025-01-15";
  return { citation: `"${title}." Available at: ${url}. Accessed: ${date}.` };
}

function saveToFile(filename, content) {
  return { status: "saved", path: `/output/${filename}`, bytes: content.length };
}

// ── Dispatcher with per-tool error handling ──────────────────
const toolFunctions = {
  web_search: (i) => webSearch(i.query),
  fetch_page: (i) => fetchPage(i.url),
  summarize_text: (i) => summarizeText(i.text, i.max_points),
  format_citation: (i) => formatCitation(i.title, i.url, i.accessed_date),
  save_to_file: (i) => saveToFile(i.filename, i.content),
};

/** Execute a tool, returning { result, isError }. Never throws. */
export async function executeTool(name, inputs) {
  const func = toolFunctions[name];
  if (!func) return { result: JSON.stringify({ error: `Unknown tool: ${name}` }), isError: true };
  try {
    const result = await func(inputs);
    return { result: JSON.stringify(result), isError: false };
  } catch (e) {
    return { result: JSON.stringify({ error: e.message, tool: name }), isError: true };
  }
}

// ── ToolRegistry: filter the toolbox by phase ────────────────
export class ToolRegistry {
  constructor() {
    this._tools = new Map();
    this._tags = new Map();
  }

  register(tool, tags = []) {
    this._tools.set(tool.function.name, tool);
    this._tags.set(tool.function.name, new Set(tags));
  }

  unregister(name) {
    this._tools.delete(name);
    this._tags.delete(name);
  }

  getToolsForContext({ tags, names } = {}) {
    if (names) return names.filter((n) => this._tools.has(n)).map((n) => this._tools.get(n));
    if (tags) {
      const tagSet = new Set(tags);
      const result = [];
      for (const [name, toolTags] of this._tags) {
        for (const t of tagSet) {
          if (toolTags.has(t)) { result.push(this._tools.get(name)); break; }
        }
      }
      return result;
    }
    return [...this._tools.values()];
  }
}

export function buildRegistry() {
  const registry = new ToolRegistry();
  registry.register(TOOLS[0], ["research", "search"]);
  registry.register(TOOLS[1], ["research", "fetch"]);
  registry.register(TOOLS[2], ["research", "analysis"]);
  registry.register(TOOLS[3], ["citation"]);
  registry.register(TOOLS[4], ["output"]);
  return registry;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const registry = buildRegistry();
  console.log("Tools, dispatcher, and registry ready.");
  console.log(`  All tools:     ${registry.getToolsForContext().map((t) => t.function.name).join(", ")}`);
  console.log(`  Research only: ${registry.getToolsForContext({ tags: ["research"] }).map((t) => t.function.name).join(", ")}`);
  console.log(`  Dispatch test: ${(await executeTool("web_search", { query: "AI agents" })).result.slice(0, 80)}...`);
  console.log(`  Error test:    ${JSON.stringify(await executeTool("fetch_page", { url: "https://broken.example.com/404" }))}`);
}
