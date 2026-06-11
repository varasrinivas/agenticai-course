/**
 * M02 Lab - Step 1: Token Counting with js-tiktoken
 * ==================================================
 * Run: node token_counting.js
 * Requires: npm install js-tiktoken
 */

import { getEncoding } from "js-tiktoken";

// Load the cl100k_base encoding (GPT-4 tokenizer — close to Mistral's for English)
const enc = getEncoding("cl100k_base");

// ── Part A: Basic token counting (COMPLETE — just read and run) ──
const samples = [
  "Hello, world!",
  "tokenization",
  "don't use pseudocode",
  "ChatGPT is one token",
  "from openai import OpenAI",
];

console.log("── Token breakdown ──");
for (const text of samples) {
  const ids = enc.encode(text);
  console.log(`${String(ids.length).padStart(3)} tokens | "${text}"`);
}
console.log();

// ── Part B: Chat message overhead (YOUR JOB) ──
function countChatTokens(messages) {
  // TODO: Implement this.
  // - Start with 3 tokens (the assistant reply primer)
  // - For each message add:
  //     4 tokens                      (role/content field markers + separator)
  //     + enc.encode(msg.role).length
  //     + enc.encode(msg.content).length
  // - Return the total
}

const messages = [
  { role: "system", content: "You are a helpful coding assistant." },
  { role: "user", content: "Explain what a token is in 2 sentences." },
];
console.log(`Chat token estimate: ${countChatTokens(messages)}`);
// Expected: ~31
