/**
 * M05 Lab - Step 2: The Agent Loop — SOLUTION
 * ============================================
 * Run: node tool_agent.js
 */

import OpenAI from "openai";
import { TOOLS, runTool } from "./tools.js";

const client = new OpenAI({ baseURL: "http://localhost:11434/v1", apiKey: "ollama" });

async function agentChat(userMessage) {
  const messages = [{ role: "user", content: userMessage }];

  while (true) {
    let response;
    try {
      response = await client.chat.completions.create({
        model: "mistral",
        tools: TOOLS,
        messages,
      });
    } catch (error) {
      return `API error: ${error.message} (is Ollama running? ollama serve)`;
    }

    const finishReason = response.choices[0].finish_reason;

    // The model is done — return the text
    if (finishReason === "stop") {
      return response.choices[0].message.content ?? "(no text response)";
    }

    // The model wants to use tools — execute them and report back
    if (finishReason === "tool_calls") {
      // The assistant message MUST be pushed before the tool results,
      // with matching tool_call_ids, or the API rejects the history
      messages.push({
        role: "assistant",
        content: null,
        tool_calls: response.choices[0].message.tool_calls,
      });

      for (const toolCall of response.choices[0].message.tool_calls) {
        const args = JSON.parse(toolCall.function.arguments); // JSON string!
        console.log(`  [tool call] ${toolCall.function.name}(${JSON.stringify(args)})`);
        const result = runTool(toolCall.function.name, args);
        console.log(`  [result]    ${result.slice(0, 80)}`);
        messages.push({ role: "tool", tool_call_id: toolCall.id, content: result });
      }
      // loop back — the model reads the results and continues
    } else {
      return `(unexpected finish_reason: ${finishReason})`;
    }
  }
}

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
