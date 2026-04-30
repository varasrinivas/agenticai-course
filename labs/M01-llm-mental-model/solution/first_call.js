/**
 * M01 Lab - Step 1: Make Your First Claude API Call — SOLUTION
 * =============================================================
 * Complete working implementation.
 */

import Anthropic from "@anthropic-ai/sdk";
import "dotenv/config";

const client = new Anthropic();

async function main() {
  console.log("--- First Claude API Call ---\n");

  try {
    const response = await client.messages.create({
      model: "claude-sonnet-4-6",
      max_tokens: 1024,
      messages: [
        {
          role: "user",
          content: "What is an AI agent? Explain in 2-3 sentences.",
        },
      ],
    });

    console.log("Response from Claude:");
    console.log(response.content[0].text);
  } catch (e) {
    if (e instanceof Anthropic.AuthenticationError) {
      console.log(
        "[ERROR] Invalid API key. Check your ANTHROPIC_API_KEY environment variable."
      );
    } else {
      console.log(`[ERROR] API call failed: ${e.message}`);
    }
  }
}

main().catch(console.error);
