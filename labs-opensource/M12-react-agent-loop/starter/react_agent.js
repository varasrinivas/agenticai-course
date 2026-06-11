/**
 * M12 Lab - Step 2: The ReAct Research Agent
 * ===========================================
 * Reason → Act → Observe → Repeat, with visible thought traces.
 * Run: node react_agent.js
 */

import OpenAI from "openai";
import { mockSearch } from "./mock_search.js";

const client = new OpenAI({ baseURL: "http://localhost:11434/v1", apiKey: "ollama" });

// The system prompt IS the ReAct pattern — it demands visible reasoning (COMPLETE)
const SYSTEM_PROMPT = `You are a research assistant that compiles accurate, well-sourced reports.

IMPORTANT: Before EVERY tool call, write:
  Thought: [your reasoning — what you know, what's missing, why THIS tool call]

After EVERY tool result, write:
  Thought: [what you learned and whether you need more information]

When you have enough information, produce a structured report with:
- Summary (2-3 sentences)
- Key Findings (bullet points)
- Sources Used (list the searches you ran)`;

const TOOLS = [{
  type: "function",
  function: {
    name: "web_search",
    description:
      "Search the web for current information about AI, technology, or " +
      "research topics. Use specific queries for better results.",
    parameters: {
      type: "object",
      properties: {
        query: {
          type: "string",
          description: "Search query — be specific (e.g., 'claude agent sdk features 2025' not 'claude')",
        },
      },
      required: ["query"],
    },
  },
}];

/** (COMPLETE) Dispatch a tool call to its implementation. */
function executeTool(name, inputs) {
  if (name === "web_search") return mockSearch(inputs.query ?? "");
  return JSON.stringify({ error: `Unknown tool: ${name}`, isError: true });
}

/**
 * Run the ReAct loop until finish_reason === "stop".
 *
 * TODO:
 * const messages = [{ role: "user", content: question }]; let turn = 0;
 * While (turn < maxTurns):
 *   1. turn++;
 *   2. response = await client.chat.completions.create({ model: "mistral",
 *        messages: [{ role: "system", content: SYSTEM_PROMPT }, ...messages],
 *        tools: TOOLS })   (try/catch → return `API error: ...`)
 *   3. const msg = response.choices[0].message;
 *   4. If verbose:
 *        log `--- Turn ${turn} ---`
 *        if (msg.content) log `Thought: ${msg.content.slice(0, 300)}`  ← ReAct!
 *        for each tc of msg.tool_calls ?? []: log tool name + args
 *   5. If finish_reason === "stop":
 *        return msg.content ?? "Agent completed without final text.";
 *   6. Push the assistant message — KEEP msg.content (the thought is part
 *      of history!): { role: "assistant", content: msg.content,
 *                      tool_calls: msg.tool_calls }
 *   7. OBSERVE: for each tc, executeTool(...), push
 *      { role: "tool", tool_call_id: tc.id, content: result }
 * After the loop: return `[Safety cap reached after ${maxTurns} turns]`;
 */
async function runAgent(question, maxTurns = 20, verbose = true) {
  // TODO: implement
}

// ── Test harness (COMPLETE) ──
const question =
  "What are the main Python frameworks for building AI agents in 2025, " +
  "and how does the claude-agent-sdk compare to them?";
const answer = await runAgent(question, 20, true);
console.log("\n" + "=".repeat(60));
console.log("FINAL REPORT:");
console.log("=".repeat(60));
console.log(answer);
