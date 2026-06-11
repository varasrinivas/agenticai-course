/**
 * M01 Lab - Step 1: Your First Chat Completion — SOLUTION
 * ========================================================
 * Run: node first_call.js
 */

import OpenAI from "openai";

const client = new OpenAI({ baseURL: "http://localhost:11434/v1", apiKey: "ollama" });

console.log("--- First Local Model Call ---\n");

try {
  const response = await client.chat.completions.create({
    model: "mistral",
    messages: [
      { role: "system", content: "You are a helpful assistant who explains things clearly." },
      { role: "user", content: "What is a large language model? Explain in 2 sentences." },
    ],
  });
  console.log(response.choices[0].message.content);
  console.log(
    `\nTokens used: ${response.usage.prompt_tokens} in, ${response.usage.completion_tokens} out`
  );
} catch (error) {
  console.error(`API error: ${error.message}`);
  console.error("Is Ollama running? Try: ollama serve");
}
