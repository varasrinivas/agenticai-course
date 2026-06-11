/**
 * M01 Lab - Step 3: Temperature Experiment — SOLUTION
 * ====================================================
 * Run: node temperature.js
 */

import OpenAI from "openai";

const client = new OpenAI({ baseURL: "http://localhost:11434/v1", apiKey: "ollama" });

const PROMPT = "Write a one-sentence description of the moon.";

for (const temp of [0.0, 1.0]) {
  console.log(`\n--- Temperature ${temp} ---`);
  for (let i = 0; i < 3; i++) {
    try {
      const response = await client.chat.completions.create({
        model: "mistral",
        temperature: temp,
        messages: [{ role: "user", content: PROMPT }],
      });
      console.log(`  Run ${i + 1}: ${response.choices[0].message.content}`);
    } catch (error) {
      console.error(`  Error: ${error.message}`);
    }
  }
}
