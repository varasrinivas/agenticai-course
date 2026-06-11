/**
 * M06 Lab - Step 2: The Orchestrating Loop — SOLUTION
 * ====================================================
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

async function runAgent(question, toolTags = null, verbose = true) {
  const activeTools = toolTags
    ? registry.getToolsForContext({ tags: toolTags })
    : registry.getToolsForContext();

  if (verbose) {
    console.log(`  Active tools: ${activeTools.map((t) => t.function.name).join(", ")}`);
  }

  const messages = [
    { role: "system", content: SYSTEM },
    { role: "user", content: question },
  ];

  for (let iteration = 0; iteration < 10; iteration++) { // safety limit
    let response;
    try {
      response = await client.chat.completions.create({
        model: "mistral",
        tools: activeTools,
        messages,
      });
    } catch (error) {
      return `API error: ${error.message}`;
    }

    const choice = response.choices[0];
    const toolCalls = choice.message.tool_calls ?? [];

    if (choice.finish_reason === "stop" || toolCalls.length === 0) {
      if (verbose) console.log(`  Agent finished in ${iteration + 1} iteration(s)`);
      return choice.message.content ?? "";
    }

    // Append assistant message (must precede the tool results)
    messages.push({
      role: "assistant",
      content: choice.message.content,
      tool_calls: toolCalls.map((tc) => ({
        id: tc.id,
        type: "function",
        function: { name: tc.function.name, arguments: tc.function.arguments },
      })),
    });

    if (verbose) {
      const mode = toolCalls.length > 1 ? "PARALLEL" : "SEQUENTIAL";
      console.log(`\n  Iteration ${iteration + 1} [${mode}]:`);
      for (const tc of toolCalls) {
        console.log(`    -> ${tc.function.name}(${tc.function.arguments.slice(0, 80)})`);
      }
    }

    // Execute tools — Promise.all gives parallelism for free
    const toolResults = await Promise.all(
      toolCalls.map(async (tc) => {
        const { result, isError } = await executeTool(tc.function.name, JSON.parse(tc.function.arguments));
        if (verbose && isError) console.log(`    [error] ${result.slice(0, 60)}`);
        return { role: "tool", tool_call_id: tc.id, content: result };
      })
    );

    messages.push(...toolResults);
  }

  return "Max iterations reached.";
}

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
