/**
 * M12 Lab - Step 2: The ReAct Research Agent — SOLUTION
 * ======================================================
 * Run: node react_agent.js
 */

import OpenAI from "openai";
import { mockSearch } from "./mock_search.js";

const client = new OpenAI({ baseURL: "http://localhost:11434/v1", apiKey: "ollama" });

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

function executeTool(name, inputs) {
  if (name === "web_search") return mockSearch(inputs.query ?? "");
  return JSON.stringify({ error: `Unknown tool: ${name}`, isError: true });
}

async function runAgent(question, maxTurns = 20, verbose = true) {
  const messages = [{ role: "user", content: question }];
  let turn = 0;

  if (verbose) console.log(`\n${"=".repeat(60)}\nQUESTION: ${question}\n${"=".repeat(60)}`);

  while (turn < maxTurns) {
    turn++;
    let response;
    try {
      response = await client.chat.completions.create({
        model: "mistral",
        messages: [{ role: "system", content: SYSTEM_PROMPT }, ...messages],
        tools: TOOLS,
      });
    } catch (error) {
      return `API error: ${error.message}`;
    }

    const msg = response.choices[0].message;

    // REASON: the thought arrives alongside any tool calls
    if (verbose) {
      console.log(`\n--- Turn ${turn} ---`);
      if (msg.content) console.log(`Thought: ${msg.content.slice(0, 300)}`);
      for (const tc of msg.tool_calls ?? []) {
        console.log(`[tool call] ${tc.function.name}(${tc.function.arguments.slice(0, 100)})`);
      }
    }

    // STOP: the model has produced its final answer
    if (response.choices[0].finish_reason === "stop") {
      return msg.content ?? "Agent completed without final text.";
    }

    // ACT: keep msg.content — the thought is part of the history
    messages.push({
      role: "assistant",
      content: msg.content,
      tool_calls: msg.tool_calls,
    });

    // OBSERVE: execute each tool call, append results as tool-role messages
    for (const tc of msg.tool_calls ?? []) {
      const result = executeTool(tc.function.name, JSON.parse(tc.function.arguments));
      if (verbose) console.log(`[observe]   ${result.slice(0, 150)}...`);
      messages.push({ role: "tool", tool_call_id: tc.id, content: result });
    }
  }

  return `[Safety cap reached after ${maxTurns} turns — partial result]`;
}

const question =
  "What are the main Python frameworks for building AI agents in 2025, " +
  "and how does the claude-agent-sdk compare to them?";
const answer = await runAgent(question, 20, true);
console.log("\n" + "=".repeat(60));
console.log("FINAL REPORT:");
console.log("=".repeat(60));
console.log(answer);
