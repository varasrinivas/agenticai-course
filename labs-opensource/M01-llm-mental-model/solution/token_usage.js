/**
 * M01 Lab - Step 4: Observe Token Usage — SOLUTION
 * =================================================
 * Run: node token_usage.js
 */

import OpenAI from "openai";

const client = new OpenAI({ baseURL: "http://localhost:11434/v1", apiKey: "ollama" });

const TESTS = [
  ["Short prompt", "Hi!", 50],
  ["Medium prompt", "Explain what a large language model is in detail.", 200],
  ["Long prompt with constraint", "Write a 3-paragraph essay about the history of computing.", 1024],
];

for (const [label, prompt, maxTok] of TESTS) {
  try {
    const response = await client.chat.completions.create({
      model: "mistral",
      max_tokens: maxTok,
      messages: [{ role: "user", content: prompt }],
    });
    const u = response.usage;
    console.log(`${label}:`);
    console.log(`  Input tokens:  ${u.prompt_tokens}`);
    console.log(`  Output tokens: ${u.completion_tokens}`);
    console.log(`  Total tokens:  ${u.prompt_tokens + u.completion_tokens}\n`);
  } catch (error) {
    console.error(`Error: ${error.message}`);
  }
}
