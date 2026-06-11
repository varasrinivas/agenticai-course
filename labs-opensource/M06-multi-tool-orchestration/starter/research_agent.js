/**
 * M06 Lab - Step 2: The Orchestrating Loop
 * =========================================
 * The M05 loop + tool filtering + max-iterations guard + PARALLEL execution.
 * Run: node research_agent.js
 */

import OpenAI from "openai";
import { buildRegistry, executeTool } from "./tools_registry.js";

const client = new OpenAI({ baseURL: "http://localhost:11434/v1", apiKey: "ollama" });
const registry = buildRegistry();

const SYSTEM =
  "You are a research assistant. When asked to compare or research multiple " +
  "topics, search for each one in parallel. When asked to fetch and summarize " +
  "a page, do it sequentially.";

/**
 * Run the multi-tool agent. Optionally filter tools by tag.
 *
 * TODO:
 * 1. const activeTools = toolTags
 *      ? registry.getToolsForContext({ tags: toolTags })
 *      : registry.getToolsForContext();
 * 2. const messages = [{ role: "system", content: SYSTEM },
 *                      { role: "user", content: question }];
 * 3. for (let iteration = 0; iteration < 10; iteration++) {   ← guard, NOT while(true)
 *    a. response = await client.chat.completions.create({ model: "mistral",
 *         tools: activeTools, messages })   (try/catch → return `API error: ...`)
 *    b. const choice = response.choices[0];
 *       const toolCalls = choice.message.tool_calls ?? [];
 *    c. If choice.finish_reason === "stop" || toolCalls.length === 0:
 *         return choice.message.content ?? "";
 *    d. Push the assistant message (content + tool_calls) onto messages
 *    e. If verbose: log "PARALLEL" if toolCalls.length > 1 else "SEQUENTIAL"
 *    f. EXECUTE:
 *       - If toolCalls.length > 1: Promise.all over the calls — each resolves to
 *         { role: "tool", tool_call_id: tc.id, content: result }
 *       - Else: await the single call
 *       REMEMBER: every tool_call_id needs a result message, including errors
 *    g. messages.push(...toolResults) and loop back
 * }
 * 4. After the loop: return "Max iterations reached.";
 */
async function runAgent(question, toolTags = null, verbose = true) {
  // TODO: implement
}

// ── Test Scenarios (COMPLETE) ──
console.log("\n> TEST 1: PARALLEL SEARCH " + "-".repeat(34));
const r1 = await runAgent(
  "Search for information about these 3 topics: AI agents, prompt engineering, and tool use patterns.",
  ["research"]
);
console.log(`\nResult preview: ${(r1 ?? "").slice(0, 200)}...`);

console.log("\n> TEST 2: SEQUENTIAL CHAIN " + "-".repeat(33));
const r2 = await runAgent(
  "Search for 'Mistral AI tool use', then fetch the first result page and summarize its content.",
  ["research"]
);
console.log(`\nResult preview: ${(r2 ?? "").slice(0, 200)}...`);

console.log("\n> TEST 3: ERROR RECOVERY " + "-".repeat(35));
const r3 = await runAgent(
  "Fetch and summarize this page: https://broken.example.com/404",
  ["research"]
);
console.log(`\nResult preview: ${(r3 ?? "").slice(0, 200)}...`);

console.log("\n> TEST 4: DYNAMIC TOOL FILTERING " + "-".repeat(27));
const r4 = await runAgent(
  "Format a citation for an article titled 'Multi-Tool AI Agents' from https://example.com/agents, accessed today.",
  ["citation"]
);
console.log(`\nResult preview: ${(r4 ?? "").slice(0, 200)}...`);
