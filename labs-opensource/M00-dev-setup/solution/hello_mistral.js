/**
 * M00 Lab - Step 2: Your First Local Model Call — SOLUTION
 * =========================================================
 * Complete working implementation.
 * Run: node hello_mistral.js
 */

import OpenAI from "openai";

// Connect to Ollama running on localhost.
// apiKey: "ollama" is a placeholder — Ollama doesn't need a real key.
const client = new OpenAI({ baseURL: "http://localhost:11434/v1", apiKey: "ollama" });

console.log("Connecting to local Mistral-7B via Ollama...");
console.log("-".repeat(50));

try {
  const response = await client.chat.completions.create({
    model: "mistral",
    messages: [
      { role: "system", content: "You are a helpful assistant. Be concise." },
      { role: "user", content: "In exactly one sentence, what is a large language model?" },
    ],
  });
  console.log(`Mistral says: ${response.choices[0].message.content}`);
  console.log("-".repeat(50));
  console.log(
    `Tokens used — input: ${response.usage.prompt_tokens}, output: ${response.usage.completion_tokens}`
  );
  console.log("\nSetup complete! Your environment is ready for the rest of the course.");
} catch (error) {
  console.error(`Error: ${error.message}`);
  console.error("\nTroubleshooting:");
  console.error("  1. Is Ollama running?    Run: ollama serve");
  console.error("  2. Is mistral pulled?    Run: ollama pull mistral");
  console.error("  3. Is openai installed?  Run: npm install openai");
}
