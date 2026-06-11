/**
 * M02 Lab - Step 1: Token Counting with js-tiktoken — SOLUTION
 * =============================================================
 * Run: node token_counting.js
 */

import { getEncoding } from "js-tiktoken";

const enc = getEncoding("cl100k_base");

// ── Part A: Basic token counting ──
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

// ── Part B: Chat message overhead ──
function countChatTokens(messages) {
  let total = 3; // primer for assistant reply
  for (const msg of messages) {
    total += 4; // role + content markers + sep
    total += enc.encode(msg.role ?? "").length;
    total += enc.encode(msg.content ?? "").length;
  }
  return total;
}

const messages = [
  { role: "system", content: "You are a helpful coding assistant." },
  { role: "user", content: "Explain what a token is in 2 sentences." },
];
console.log(`Chat token estimate: ${countChatTokens(messages)}`);
// Output: Chat token estimate: ~31
