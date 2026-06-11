/**
 * M08 Lab - Step 3: SmartConversationManager
 * ===========================================
 * Auto-summarization when input tokens cross a threshold + JSON persistence.
 * Run: node smart_manager.js
 */

import OpenAI from "openai";
import { readFileSync, writeFileSync } from "node:fs";

import { pathToFileURL } from "node:url";
const client = new OpenAI({ baseURL: "http://localhost:11434/v1", apiKey: "ollama" });

export class SmartConversationManager {
  constructor({
    systemPrompt = "You are a helpful assistant.",
    model = "mistral",
    tokenThreshold = 8_000,   // lower for Mistral's 32K context
    recentTurnsToKeep = 4,
  } = {}) {
    this.systemPrompt = systemPrompt;
    this.model = model;
    this.messages = [];
    this.tokenThreshold = tokenThreshold;
    this.recentTurnsToKeep = recentTurnsToKeep;
    this.summary = null;
    this.summaryHistory = [];
    this.lastInputTokens = 0;
    this.totalInputTokens = 0;
    this.totalOutputTokens = 0;
  }

  /** (COMPLETE) */
  _shouldSummarize() {
    return this.lastInputTokens > this.tokenThreshold;
  }

  /**
   * Use Mistral to summarize older messages.
   *
   * TODO:
   * 1. const keepCount = this.recentTurnsToKeep * 2;  (user+assistant pairs)
   *    If this.messages.length <= keepCount: return (nothing to do)
   * 2. const oldMessages = this.messages.slice(0, -keepCount);
   *    const recentMessages = this.messages.slice(-keepCount);
   * 3. Build a summary prompt:
   *    "Summarize this conversation concisely. Preserve: key decisions,
   *     user preferences, important facts. Skip: greetings, filler.\n\n"
   *    + one "role: content" line per old message
   * 4. Call the model (system: "You are a conversation summarizer. Be concise.")
   * 5. If this.summary already exists, chain it:
   *    newSummary = `Previous context: ${this.summary}\n\nRecent: ${newSummary}`
   * 6. Set this.summary, push { timestamp: Date.now(),
   *    messagesSummarized: oldMessages.length } onto this.summaryHistory
   * 7. Replace this.messages with:
   *    [{ role: "user", content: `[Conversation summary: ${this.summary}]` },
   *     { role: "assistant", content: "Understood. I have the conversation context." },
   *     ...recentMessages]
   * 8. On ANY error: this.messages = recentMessages  ← graceful fallback,
   *    never crash the conversation because a summary failed
   */
  async _summarizeOldMessages() {
    // TODO: implement
  }

  /**
   * Send with automatic summarization when needed.
   *
   * TODO:
   * 1. Push the user message
   * 2. Call the API with [system, ...this.messages]
   * 3. Record usage: this.lastInputTokens = usage.prompt_tokens, and
   *    accumulate the running totals
   * 4. Push + capture the assistant text
   * 5. AFTER the successful reply: if (this._shouldSummarize())
   *      await this._summarizeOldMessages();
   * 6. Return the assistant text
   * 7. On error: pop the user message, throw
   */
  async send(userMessage) {
    // TODO: implement
  }

  // ── Persistence (COMPLETE) ──
  save(filepath) {
    const state = {
      systemPrompt: this.systemPrompt,
      model: this.model,
      messages: this.messages,
      summary: this.summary,
      summaryHistory: this.summaryHistory,
      totalInputTokens: this.totalInputTokens,
      totalOutputTokens: this.totalOutputTokens,
      savedAt: Date.now(),
    };
    writeFileSync(filepath, JSON.stringify(state, null, 2));
  }

  static load(filepath) {
    const data = JSON.parse(readFileSync(filepath, "utf-8"));
    const mgr = new SmartConversationManager({
      systemPrompt: data.systemPrompt,
      model: data.model,
    });
    mgr.messages = data.messages;
    mgr.summary = data.summary ?? null;
    mgr.summaryHistory = data.summaryHistory ?? [];
    mgr.totalInputTokens = data.totalInputTokens ?? 0;
    mgr.totalOutputTokens = data.totalOutputTokens ?? 0;
    return mgr;
  }
}

// ── Test harness (COMPLETE) ──
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const manager = new SmartConversationManager({
    tokenThreshold: 3_000,
    recentTurnsToKeep: 4,
    systemPrompt: "You are a helpful coding assistant.",
  });

  const turns = [
    "Help me build a REST API with FastAPI. Explain the project structure in detail.",
    "Now explain how to add a database with SQLAlchemy, including models and migrations.",
    "Add JWT authentication with refresh tokens. Show the full flow.",
    "How do I write tests for all of this with pytest?",
    "What about deployment — Docker, environment variables, the works?",
  ];
  for (let i = 0; i < turns.length; i++) {
    await manager.send(turns[i]);
    console.log(
      `Turn ${i + 1}: last_input=${manager.lastInputTokens} tokens, stored=${manager.messages.length} msgs`
    );
  }

  console.log(`\nSummaries created: ${manager.summaryHistory.length}`);

  manager.save("conversation_state.json");
  const restored = SmartConversationManager.load("conversation_state.json");
  console.log(`Restored: ${restored.messages.length} messages, summary=${restored.summary ? "yes" : "no"}`);
  console.log(`\nRestored agent says: ${(await restored.send("Where were we? One sentence.")).slice(0, 200)}`);
}
