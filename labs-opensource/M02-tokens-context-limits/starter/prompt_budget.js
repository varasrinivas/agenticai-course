/**
 * M02 Lab - Step 2: The PromptBudget Class
 * =========================================
 * Track token usage across a conversation and auto-truncate when it won't fit.
 * Run: node prompt_budget.js
 * Requires: npm install js-tiktoken openai
 */

import { getEncoding } from "js-tiktoken";
import OpenAI from "openai";

class PromptBudget {
  // Per-message overhead in cl100k_base terms
  TOKENS_PER_MESSAGE = 4;   // role + content markers + sep
  TOKENS_REPLY_PRIMER = 3;  // assistant reply primer tokens

  constructor(model = "mistral", maxContext = 32_000) {
    this.model = model;
    this.maxContext = maxContext;
    // cl100k_base is a close approximation for Mistral
    this.enc = getEncoding("cl100k_base");
  }

  /** Count tokens in a plain string. (COMPLETE) */
  estimateTokens(text) {
    return this.enc.encode(text).length;
  }

  /** Count tokens for a messages list including overhead. (COMPLETE) */
  countMessages(messages) {
    let total = this.TOKENS_REPLY_PRIMER;
    for (const msg of messages) {
      total += this.TOKENS_PER_MESSAGE;
      total += this.enc.encode(msg.role ?? "").length;
      total += this.enc.encode(msg.content ?? "").length;
    }
    return total;
  }

  /** Rough estimate: serialize tools to JSON and count. (COMPLETE) */
  countTools(tools) {
    if (!tools || tools.length === 0) return 0;
    return this.enc.encode(JSON.stringify(tools)).length;
  }

  /**
   * Return how many tokens are left for new messages + output.
   * TODO: used = this.countMessages(messages) + this.countTools(tools);
   *       return this.maxContext - used - reserveOutput;
   */
  remaining(messages, tools = undefined, reserveOutput = 512) {
    // TODO: implement
  }

  /**
   * True if adding `text` as a new message still fits in budget.
   * TODO: the new message costs estimateTokens(text) + TOKENS_PER_MESSAGE.
   *       Compare against this.remaining(...).
   */
  fits(text, messages, tools = undefined, reserveOutput = 512) {
    // TODO: implement
  }

  /**
   * Drop oldest non-system messages until the conversation fits.
   * TODO:
   * - Work on a COPY of messages (don't mutate the input)
   * - If the first message is the system prompt, never drop it
   *   (start dropping from index 1, else index 0)
   * - While countMessages(result) + reserveOutput > maxContext:
   *     - stop if only the system prompt + one message remain
   *     - otherwise splice out the oldest non-system message
   * - Return the new array
   */
  truncateHistory(messages, reserveOutput = 512) {
    // TODO: implement
  }
}

// ── Demo: 4-turn conversation with budget checks (COMPLETE) ──
const budget = new PromptBudget("mistral", 32_000);
const client = new OpenAI({ baseURL: "http://localhost:11434/v1", apiKey: "ollama" });

const system = { role: "system", content: "You are a concise coding assistant." };
let history = [system];

const turns = [
  "What is a Python list comprehension?",
  "Show me an example that squares even numbers from 1 to 20.",
  "How does that compare to a regular for-loop?",
  "What's the memory usage difference?",
];

for (const userText of turns) {
  console.log(`\nUser: ${userText}`);
  console.log(`  Tokens remaining: ${budget.remaining(history)}`);

  if (!budget.fits(userText, history)) {
    console.log("  [truncating history to fit]");
    history = budget.truncateHistory(history);
  }

  history.push({ role: "user", content: userText });

  try {
    const response = await client.chat.completions.create({
      model: "mistral",
      messages: history,
      max_tokens: 256,
    });
    const reply = response.choices[0].message.content ?? "";
    history.push({ role: "assistant", content: reply });
    console.log(`Assistant: ${reply.slice(0, 120)}...`);
  } catch (err) {
    console.error(`  Error: ${err.message}`);
    history.pop(); // keep state consistent
  }
}
