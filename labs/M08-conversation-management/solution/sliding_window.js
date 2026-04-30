/**
 * M08 Lab - Step 2: Sliding Window Conversation Manager (Solution)
 * =================================================================
 * Complete solution: a SlidingWindowManager that drops the oldest messages
 * when the conversation exceeds a token budget.
 *
 * Usage:
 *     node sliding_window.js
 */

import Anthropic from "@anthropic-ai/sdk";
import "dotenv/config";

const client = new Anthropic();
const MODEL = "claude-sonnet-4-6";

const SYSTEM_PROMPT =
  "You are a UCC filing research assistant. Help users understand " +
  "UCC filings, lien risks, and secured transactions. Provide clear, " +
  "concise answers.";

// =============================================================================
// OBSERVATION HELPERS
// =============================================================================

function observe(label, message) {
  console.log(`\n${"=".repeat(60)}`);
  console.log(`[${label}] ${message}`);
  console.log("=".repeat(60));
}

function observeTokens(tokenCount, maxTokens, messageCount) {
  console.log(`[TOKENS] ~${tokenCount} / ${maxTokens}`);
  console.log(`[HISTORY] ${messageCount} messages in history`);
}

function observeWindow(dropped, tokensFreed) {
  console.log(
    `[WINDOW] Dropped ${dropped} oldest messages (${tokensFreed} tokens freed)`
  );
}

// =============================================================================
// SOLUTION: SlidingWindowManager
// =============================================================================

class SlidingWindowManager {
  constructor(systemPrompt = SYSTEM_PROMPT, maxTokens = 2048) {
    this.systemPrompt = systemPrompt;
    this.maxTokens = maxTokens;
    // Step 1: Initialize empty messages array
    this.messages = [];
  }

  _estimateTokens(messages) {
    // Step 2: Estimate tokens
    return Math.floor(
      (this.systemPrompt.length + JSON.stringify(messages).length) / 4
    );
  }

  _trimHistory() {
    // Step 3: Drop oldest message pairs until under budget
    while (
      this._estimateTokens(this.messages) > this.maxTokens &&
      this.messages.length > 2
    ) {
      const tokensBefore = this._estimateTokens(this.messages);

      let droppedCount = 0;
      // Remove first message
      this.messages.shift();
      droppedCount++;
      // If next message is assistant, remove it too to maintain pairing
      if (this.messages.length > 2 && this.messages[0].role === "assistant") {
        this.messages.shift();
        droppedCount++;
      }

      const tokensAfter = this._estimateTokens(this.messages);
      observeWindow(droppedCount, tokensBefore - tokensAfter);
    }
  }

  addUserMessage(text) {
    // Step 4: Push user message
    this.messages.push({ role: "user", content: text });
  }

  async send() {
    // Step 5: Trim history, then call API
    this._trimHistory();

    const response = await client.messages.create({
      model: MODEL,
      max_tokens: 1024,
      system: this.systemPrompt,
      messages: this.messages,
    });

    // Step 6: Extract text and push to history
    let assistantText = "";
    for (const block of response.content) {
      if (block.text) {
        assistantText += block.text;
      }
    }

    this.messages.push({ role: "assistant", content: assistantText });

    return assistantText;
  }

  getHistory() {
    // Step 7: Return messages
    return this.messages;
  }

  getTokenCount() {
    return this.messages.length > 0 ? this._estimateTokens(this.messages) : 0;
  }
}

// =============================================================================
// MAIN
// =============================================================================

console.log("=".repeat(60));
console.log("M08 Lab - Step 2: Sliding Window Conversation Manager (SOLUTION)");
console.log("=".repeat(60));

const manager = new SlidingWindowManager(SYSTEM_PROMPT, 2048);
console.log(`Token budget: ${manager.maxTokens} tokens`);

const testQuestions = [
  "What is a UCC-1 filing?",
  "Who files a UCC-1?",
  "What is the purpose of perfecting a security interest?",
  "What collateral types can be covered by a UCC filing?",
  "What is a continuation statement?",
  "What is a UCC-3 amendment?",
  "How do I search for existing UCC filings?",
  "What are the risks of not filing a UCC-1?",
  "What is a purchase money security interest?",
  "How do UCC filings work in bankruptcy?",
  "What is a blanket lien?",
  "Summarize what we discussed",
];

for (let i = 0; i < testQuestions.length; i++) {
  const question = testQuestions[i];
  console.log(`\n--- Turn ${i + 1}/${testQuestions.length} ---`);

  observe("USER", question);
  manager.addUserMessage(question);

  const response = await manager.send();

  observe(
    "ASSISTANT",
    response.length > 200 ? response.slice(0, 200) + "..." : response
  );
  observeTokens(
    manager.getTokenCount(),
    manager.maxTokens,
    manager.getHistory().length
  );
}

console.log(`\n${"=".repeat(60)}`);
console.log(
  `Final: ${manager.getHistory().length} messages visible ` +
    `(window dropped older messages to stay under ${manager.maxTokens})`
);
console.log("=".repeat(60));
