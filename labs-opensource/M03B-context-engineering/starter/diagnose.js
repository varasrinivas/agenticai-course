/**
 * M03B Lab: diagnose.js (COMPLETE — runs against YOUR context_budget.js)
 * ========================================================================
 * Demonstrates the poisoned-transcript effect and the fix.
 * Run: node diagnose.js
 */

import { readFileSync } from "node:fs";
import OpenAI from "openai";
import { ContextBudget, summarizeHistory } from "./context_budget.js";

const client = new OpenAI({ baseURL: "http://localhost:11434/v1", apiKey: "ollama" });

async function askModel(budget) {
  const { system, messages } = budget.buildMessages();
  const t0 = Date.now();
  try {
    const response = await client.chat.completions.create({
      model: "mistral",
      messages: [{ role: "system", content: system }, ...messages],
      max_tokens: 300,
    });
    return [
      response.choices[0].message.content ?? "",
      {
        input_tokens: response.usage?.prompt_tokens ?? 0,
        output_tokens: response.usage?.completion_tokens ?? 0,
        latency_s: (Date.now() - t0) / 1000,
      },
    ];
  } catch (e) {
    return [`[error: ${e.message}]`, { input_tokens: 0, output_tokens: 0, latency_s: 0 }];
  }
}

const fixture = JSON.parse(readFileSync(new URL("./poisoned_transcript.json", import.meta.url), "utf-8"));

const baseArgs = {
  model: "mistral",
  systemPrompt: fixture.system_prompt,
  toolDefinitions: fixture.tool_definitions,
  history: fixture.history,
  currentUserMessage: fixture.current_user_message,
};

// --- Run 1: rotted context ---
const rotted = new ContextBudget(baseArgs);
console.log("=== Token Breakdown (rotted) ===");
for (const [layer, tok] of Object.entries(rotted.account())) {
  console.log(`  ${layer.padEnd(15)}: ${tok.toLocaleString()} tokens`);
}
console.log(
  `  ${"TOTAL".padEnd(15)}: ${rotted.total().toLocaleString()} / ${rotted.maxTokens.toLocaleString()}  strategy=${rotted.strategy()}`
);

console.log("\n>>> Run 1: ROTTED context (no fix)");
const [answerA, usageA] = await askModel(rotted);
console.log(`Tokens: ${usageA.input_tokens} in, ${usageA.output_tokens} out  (${usageA.latency_s.toFixed(2)}s)`);
console.log(`Answer: ${answerA}\n`);

// --- Run 2: after checkpoint ---
const fixed = new ContextBudget({ ...baseArgs, history: [...fixture.history] });
fixed.history = await summarizeHistory(fixed.history, 4);
console.log(">>> Run 2: COMPRESSED context (after checkpoint)");
console.log(`  Total after compression: ${fixed.total().toLocaleString()} tokens  strategy=${fixed.strategy()}`);
const [answerB, usageB] = await askModel(fixed);
console.log(`Tokens: ${usageB.input_tokens} in, ${usageB.output_tokens} out  (${usageB.latency_s.toFixed(2)}s)`);
console.log(`Answer: ${answerB}\n`);

console.log("=".repeat(60));
console.log(`Token delta:   ${usageA.input_tokens - usageB.input_tokens} input tokens`);
console.log(`Latency delta: ${(usageA.latency_s - usageB.latency_s).toFixed(2)}s`);
console.log("\nSuccess check: Run 2 must still cite ORD-88421 and November 3rd.");
