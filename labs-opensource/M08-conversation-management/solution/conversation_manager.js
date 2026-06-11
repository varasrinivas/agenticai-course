/**
 * M08 Lab - Steps 1+2: ConversationManager + SlidingWindowManager — SOLUTION
 * ===========================================================================
 * Run: node conversation_manager.js
 */

import OpenAI from "openai";

import { pathToFileURL } from "node:url";
const client = new OpenAI({ baseURL: "http://localhost:11434/v1", apiKey: "ollama" });

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

  getMessages() {
    return [{ role: "system", content: this.systemPrompt }, ...this.messages];
  }

  async send(userMessage) {
    this.addUserMessage(userMessage);
    try {
      const response = await client.chat.completions.create({
        model: this.model,
        messages: this.getMessages(),
      });
      if (response.usage) {
        this.totalInputTokens += response.usage.prompt_tokens;
        this.totalOutputTokens += response.usage.completion_tokens;
      }
      const assistantText = response.choices[0].message.content;
      this.addAssistantMessage(assistantText);
      return assistantText;
    } catch (error) {
      this.messages.pop(); // remove failed user message
      throw new Error(`API call failed: ${error.message}`);
    }
  }

  getTokenUsage() {
    return {
      totalInput: this.totalInputTokens,
      totalOutput: this.totalOutputTokens,
      messages: this.messages.length,
    };
  }
}

export class SlidingWindowManager extends ConversationManager {
  constructor({ windowSize = 10, ...opts } = {}) {
    super(opts);
    this.windowSize = windowSize;
  }

  getMessages() {
    let windowed = this.messages.length <= this.windowSize
      ? [...this.messages]
      : this.messages.slice(-this.windowSize);

    // History sent to the API should start with a user turn
    if (windowed[0]?.role === "assistant") {
      windowed = windowed.slice(1);
    }
    return [{ role: "system", content: this.systemPrompt }, ...windowed];
  }
}

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
