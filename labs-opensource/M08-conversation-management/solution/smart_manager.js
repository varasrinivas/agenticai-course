/**
 * M08 Lab - Step 3: SmartConversationManager — SOLUTION
 * ======================================================
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
    tokenThreshold = 8_000,
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

  _shouldSummarize() {
    return this.lastInputTokens > this.tokenThreshold;
  }

  async _summarizeOldMessages() {
    const keepCount = this.recentTurnsToKeep * 2; // user+assistant pairs
    if (this.messages.length <= keepCount) return;

    const oldMessages = this.messages.slice(0, -keepCount);
    const recentMessages = this.messages.slice(-keepCount);

    let summaryPrompt =
      "Summarize this conversation concisely. " +
      "Preserve: key decisions, user preferences, important facts. " +
      "Skip: greetings, filler.\n\n";
    for (const msg of oldMessages) {
      summaryPrompt += `${msg.role}: ${msg.content}\n`;
    }

    try {
      const response = await client.chat.completions.create({
        model: this.model,
        messages: [
          { role: "system", content: "You are a conversation summarizer. Be concise." },
          { role: "user", content: summaryPrompt },
        ],
      });
      let newSummary = response.choices[0].message.content;

      if (this.summary) {
        newSummary = `Previous context: ${this.summary}\n\nRecent: ${newSummary}`;
      }

      this.summary = newSummary;
      this.summaryHistory.push({
        timestamp: Date.now(),
        messagesSummarized: oldMessages.length,
      });

      this.messages = [
        { role: "user", content: `[Conversation summary: ${this.summary}]` },
        { role: "assistant", content: "Understood. I have the conversation context." },
        ...recentMessages,
      ];
    } catch {
      // Graceful fallback: plain truncation. Never crash the conversation.
      this.messages = recentMessages;
    }
  }

  async send(userMessage) {
    this.messages.push({ role: "user", content: userMessage });

    try {
      const response = await client.chat.completions.create({
        model: this.model,
        messages: [{ role: "system", content: this.systemPrompt }, ...this.messages],
      });

      if (response.usage) {
        this.lastInputTokens = response.usage.prompt_tokens;
        this.totalInputTokens += response.usage.prompt_tokens;
        this.totalOutputTokens += response.usage.completion_tokens;
      }

      const assistantText = response.choices[0].message.content;
      this.messages.push({ role: "assistant", content: assistantText });

      if (this._shouldSummarize()) {
        await this._summarizeOldMessages();
      }

      return assistantText;
    } catch (error) {
      this.messages.pop();
      throw new Error(`API call failed: ${error.message}`);
    }
  }

  // ── Persistence ──
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
    console.log(`Turn ${i + 1}: last_input=${manager.lastInputTokens} tokens, stored=${manager.messages.length} msgs`);
  }

  console.log(`\nSummaries created: ${manager.summaryHistory.length}`);

  manager.save("conversation_state.json");
  const restored = SmartConversationManager.load("conversation_state.json");
  console.log(`Restored: ${restored.messages.length} messages, summary=${restored.summary ? "yes" : "no"}`);
  console.log(`\nRestored agent says: ${(await restored.send("Where were we? One sentence.")).slice(0, 200)}`);
}
