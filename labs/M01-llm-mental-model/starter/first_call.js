/**
 * M01 Lab - Step 1: Make Your First Claude API Call
 * ==================================================
 * Complete the TODO below to send a message to Claude and print the response.
 */

import Anthropic from "@anthropic-ai/sdk";
import "dotenv/config";

// Create the Anthropic client (reads ANTHROPIC_API_KEY automatically)
const client = new Anthropic();

async function main() {
  console.log("--- First Claude API Call ---\n");

  // TODO: Use client.messages.create() to send a message to Claude
  // - model: "claude-sonnet-4-6"
  // - max_tokens: 1024
  // - messages: a single user message asking "What is an AI agent? Explain in 2-3 sentences."
  // Then print the response text.
  //
  // Hint: The response text lives at response.content[0].text

  return; // Remove this line when you add your code
}

main().catch(console.error);
