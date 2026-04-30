/**
 * M01 Lab - Step 3: Model Comparison — SOLUTION
 * ================================================
 * Complete working implementation.
 */

import Anthropic from "@anthropic-ai/sdk";
import "dotenv/config";

const client = new Anthropic();

/**
 * Call a specific Claude model and return the response text and elapsed time.
 * @param {string} modelName - The model identifier
 * @param {string} prompt - The prompt to send
 * @returns {Promise<[string, number]>} [response_text, elapsed_seconds]
 */
async function callModel(modelName, prompt) {
  const start = performance.now();
  const response = await client.messages.create({
    model: modelName,
    max_tokens: 1024,
    messages: [{ role: "user", content: prompt }],
  });
  const elapsed = (performance.now() - start) / 1000;
  return [response.content[0].text, elapsed];
}

async function main() {
  const prompt = "Explain what a UCC filing is in 2-3 sentences.";
  const models = [
    "claude-haiku-4-5-20251001",
    "claude-sonnet-4-6",
  ];

  console.log("--- Model Comparison ---\n");
  for (const model of models) {
    console.log(`Model: ${model}`);
    try {
      const [text, elapsed] = await callModel(model, prompt);
      console.log(`Time: ${elapsed.toFixed(2)}s`);
      console.log(`Response:\n  ${text}\n`);
    } catch (e) {
      console.log(`  [ERROR] ${e.message}\n`);
    }
  }
}

main().catch(console.error);
