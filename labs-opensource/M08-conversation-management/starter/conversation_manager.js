/**
 * M08 Lab - Steps 1+2: ConversationManager + SlidingWindowManager
 * ================================================================
 * Run: node conversation_manager.js
 */

import OpenAI from "openai";

import { pathToFileURL } from "node:url";
const client = new OpenAI({ baseURL: "http://localhost:11434/v1", apiKey: "ollama" });

// ── Step 1: Basic ConversationManager ────────────────────────
export class ConversationManager {
  constructor({ systemPrompt = "You are a helpful assistant.", model = "mistral" } = {}) {
    this.systemPrompt = systemPrompt;
    this.model = model;
    this.messages = [];
    this.totalInputTokens = 0;
    this.totalOutputTokens = 0;
  }

  addUserMessage(content) {
    this.messages.push({ role: "user", content });
  }

  addAssistantMessage(content) {
    this.messages.push({ role: "assistant", content });
  }

  /** Return messages with system prompt prepended. (COMPLETE) */
  getMessages() {
    return [{ role: "system", content: this.systemPrompt }, ...this.messages];
  }

  /**
   * Send a message and get the model's response.
   *
   * TODO:
   * 1. this.addUserMessage(userMessage);
   * 2. response = await client.chat.completions.create({ model: this.model,
   *      messages: this.getMessages() });
   * 3. If response.usage: accumulate prompt_tokens / completion_tokens
   *    into this.totalInputTokens / this.totalOutputTokens
   * 4. Push + return the assistant text
   * 5. On error: this.messages.pop() (remove the failed user message),
   *    then throw new Error(`API call failed: ${error.message}`)
   */
  async send(userMessage) {
    // TODO: implement
  }

  getTokenUsage() {
    return {
      totalInput: this.totalInputTokens,
      totalOutput: this.totalOutputTokens,
      messages: this.messages.length,
    };
  }
}

// ── Step 2: SlidingWindowManager ─────────────────────────────
export class SlidingWindowManager extends ConversationManager {
  constructor({ windowSize = 10, ...opts } = {}) {
    super(opts);
    this.windowSize = windowSize;
  }

  /**
   * Return system prompt + only the most recent N messages.
   *
   * TODO:
   * 1. let windowed = the last this.windowSize entries of this.messages
   *    (or all of them if there are fewer)
   * 2. GOTCHA: if windowed starts with an "assistant" message, drop it —
   *    history sent to the API should start with a user turn
   * 3. Return [{ role: "system", ... }, ...windowed]
   */
  getMessages() {
    // TODO: implement
  }
}

// ── Test harness (COMPLETE) ──────────────────────────────────
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  console.log("=".repeat(50));
  console.log("TEST 1: Basic ConversationManager (full history)");
  console.log("=".repeat(50));
  const mgr = new ConversationManager({ systemPrompt: "You are a concise coding tutor. Answer in 1-2 sentences." });
  for (const q of ["What is a list comprehension in Python?", "Show me an example with filtering."]) {
    console.log(`\nQ: ${q}`);
    console.log(`A: ${(await mgr.send(q)).slice(0, 150)}`);
    console.log(`   usage so far:`, mgr.getTokenUsage());
  }

  console.log("\n" + "=".repeat(50));
  console.log("TEST 2: SlidingWindowManager (windowSize=6)");
  console.log("=".repeat(50));
  const win = new SlidingWindowManager({ windowSize: 6, systemPrompt: "You are a concise coding tutor." });
  for (const q of ["What is Python?", "What are variables?", "Explain loops.",
                   "What are functions?", "Explain classes.", "What is inheritance?"]) {
    await win.send(q);
    console.log(`Q: ${q}  (stored=${win.messages.length}, sent=${win.getMessages().length - 1})`);
  }

  console.log(`\nStored: ${win.messages.length} messages`);
  console.log(`Sent (excl. system): ${win.getMessages().length - 1} messages`);
}
