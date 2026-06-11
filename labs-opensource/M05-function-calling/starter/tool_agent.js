/**
 * M05 Lab - Step 2: The Agent Loop
 * =================================
 * The tools are provided (tools.js). You build the loop that lets the model
 * use them: call → check finish_reason → execute tools → report back → repeat.
 * Run: node tool_agent.js
 */

import OpenAI from "openai";
import { TOOLS, runTool } from "./tools.js";

const client = new OpenAI({ baseURL: "http://localhost:11434/v1", apiKey: "ollama" });

/**
 * Run the full agent loop: send message, handle tool calls, return final answer.
 *
 * TODO:
 * const messages = [{ role: "user", content: userMessage }];
 * Loop forever:
 *   1. response = await client.chat.completions.create({ model: "mistral",
 *        tools: TOOLS, messages })
 *      — wrap in try/catch, return `API error: ${error.message}` on failure
 *   2. const finishReason = response.choices[0].finish_reason;
 *   3. If finishReason === "stop":
 *        return response.choices[0].message.content ?? "(no text response)";
 *   4. If finishReason === "tool_calls":
 *      a. FIRST push the assistant message onto history:
 *         messages.push({ role: "assistant", content: null,
 *                         tool_calls: response.choices[0].message.tool_calls });
 *      b. For each toolCall of response.choices[0].message.tool_calls:
 *         - const args = JSON.parse(toolCall.function.arguments);  // JSON STRING!
 *         - console.log(`  [tool call] ${toolCall.function.name}(${JSON.stringify(args)})`);
 *         - const result = runTool(toolCall.function.name, args);
 *         - console.log(`  [result]    ${result.slice(0, 80)}`);
 *         - messages.push({ role: "tool", tool_call_id: toolCall.id, content: result });
 *      c. Loop back to 1 — the model reads the results and continues
 *   5. Anything else: return `(unexpected finish_reason: ${finishReason})`;
 *
 * GOTCHA: the assistant message (4a) MUST come before the tool results (4b),
 * with matching tool_call_ids — otherwise the API rejects the history.
 */
async function agentChat(userMessage) {
  // TODO: implement
}

// ── Test harness (COMPLETE) ──
const testQuestions = [
  "What's the weather like in Tokyo?",
  "What is (15 * 7) + 23?",
  "What time is it in London?",
  "What's the capital of France?", // No tool needed!
];

for (const q of testQuestions) {
  console.log(`\n${"=".repeat(50)}`);
  console.log(`User: ${q}`);
  const answer = await agentChat(q);
  console.log(`Agent: ${(answer ?? "").slice(0, 150)}`);
}
