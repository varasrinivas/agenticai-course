/**
 * M01 Lab - Step 2: Temperature Experiment — SOLUTION
 * =====================================================
 * Complete working implementation.
 */

import Anthropic from "@anthropic-ai/sdk";
import "dotenv/config";

const client = new Anthropic();
const MODEL = "claude-sonnet-4-20250514";

/**
 * Call Claude with a specific temperature and return the response text.
 * @param {string} prompt - The prompt to send
 * @param {number} temp - Temperature value (0.0 to 1.0)
 * @returns {Promise<string>} The response text
 */
async function callWithTemperature(prompt, temp) {
  const response = await client.messages.create({
    model: MODEL,
    max_tokens: 256,
    temperature: temp,
    messages: [{ role: "user", content: prompt }],
  });
  return response.content[0].text;
}

async function main() {
  const prompt = "Write a one-sentence tagline for an AI coding assistant.";
  const temperatures = [0.0, 0.5, 1.0];

  console.log("--- Temperature Experiment ---\n");
  for (const temp of temperatures) {
    console.log(`Temperature ${temp}:`);
    try {
      const result = await callWithTemperature(prompt, temp);
      console.log(`  "${result}"\n`);
    } catch (e) {
      console.log(`  [ERROR] ${e.message}\n`);
    }
  }
}

main().catch(console.error);
