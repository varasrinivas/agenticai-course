/**
 * M02 Lab - Step 2: The PromptBudget Class — SOLUTION
 * ====================================================
 * Run: node prompt_budget.js
 */

import { getEncoding } from "js-tiktoken";
import OpenAI from "openai";

class PromptBudget {
  TOKENS_PER_MESSAGE = 4;   // role + content markers + sep
  TOKENS_REPLY_PRIMER = 3;  // assistant reply primer tokens

  constructor(model = "mistral", maxContext = 32_000) {
    this.model = model;
    this.maxContext = maxContext;
    this.enc = getEncoding("cl100k_base");
  }

  estimateTokens(text) {
    return this.enc.encode(text).length;
  }

  countMessages(messages) {
    let total = this.TOKENS_REPLY_PRIMER;
    for (const msg of messages) {
      total += this.TOKENS_PER_MESSAGE;
      total += this.enc.encode(msg.role ?? "").length;
      total += this.enc.encode(msg.content ?? "").length;
    }
    return total;
  }

  countTools(tools) {
    if (!tools || tools.length === 0) return 0;
    return this.enc.encode(JSON.stringify(tools)).length;
  }

  remaining(messages, tools = undefined, reserveOutput = 512) {
    const used = this.countMessages(messages) + this.countTools(tools);
    return this.maxContext - used - reserveOutput;
  }

  fits(text, messages, tools = undefined, reserveOutput = 512) {
    const newMsgTokens = this.estimateTokens(text) + this.TOKENS_PER_MESSAGE;
    return this.remaining(messages, tools, reserveOutput) >= newMsgTokens;
  }

  truncateHistory(messages, reserveOutput = 512) {
    const result = [...messages];
    const start = result[0]?.role === "system" ? 1 : 0;

    while (true) {
      const tokensUsed = this.countMessages(result);
      const headroom = this.maxContext - tokensUsed - reserveOutput;
      if (headroom >= 0) break;
      if (result.length <= start + 1) break;
      result.splice(start, 1); // remove oldest non-system message
    }
    return result;
  }
}

// ── Demo: 4-turn conversation with budget checks ──
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
    history.pop();
  }
}
