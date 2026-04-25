/**
 * M08 Lab - Step 2: Sliding Window Conversation Manager (Starter)
 * ================================================================
 * Build a SlidingWindowManager that drops the oldest messages when the
 * conversation exceeds a token budget.
 *
 * KEY CONCEPT: Full history works for short conversations, but tokens cost
 * money and context windows have limits. A sliding window keeps only the
 * most recent messages, trading long-term memory for cost control.
 *
 * Usage:
 *     node sliding_window.js
 */

import Anthropic from "@anthropic-ai/sdk";
import "dotenv/config";

const client = new Anthropic();
const MODEL = "claude-sonnet-4-20250514";

const SYSTEM_PROMPT =
  "You are a UCC filing research assistant. Help users understand " +
  "UCC filings, lien risks, and secured transactions. Provide clear, " +
  "concise answers.";

// =============================================================================
// OBSERVATION HELPERS (complete -- do not modify)
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
// YOUR CODE: Implement SlidingWindowManager
// =============================================================================

class SlidingWindowManager {
  /**
   * Manages conversation history with a sliding window that drops
   * oldest messages when the token budget is exceeded.
   */

  constructor(systemPrompt = SYSTEM_PROMPT, maxTokens = 2048) {
    this.systemPrompt = systemPrompt;
    this.maxTokens = maxTokens;
    // ------------------------------------------------------------------
    // TODO 1: Initialize an empty array to store messages.
    // ------------------------------------------------------------------
    this.messages = null; // Replace with correct initialization
  }

  _estimateTokens(messages) {
    /**
     * Estimate token count for a list of messages.
     * Uses Math.floor(str.length / 4) as a simple heuristic.
     * Include the system prompt in the estimate.
     */
    // ------------------------------------------------------------------
    // TODO 2: Estimate tokens for the given messages plus system prompt.
    // Use: Math.floor((this.systemPrompt.length + JSON.stringify(messages).length) / 4)
    // ------------------------------------------------------------------
    return 0;
  }

  _trimHistory() {
    /**
     * Trim oldest messages to stay within token budget.
     * Keep removing the oldest message pair (index 0, 1) until the
     * estimated token count is under this.maxTokens.
     *
     * IMPORTANT: Never drop all messages -- always keep at least the
     * last 2 messages (the most recent user + assistant pair).
     */
    // ------------------------------------------------------------------
    // TODO 3: While _estimateTokens(this.messages) > this.maxTokens
    //   and this.messages.length > 2:
    //
    //   a) Record the token count BEFORE trimming.
    //   b) Remove messages from the front of the array, 2 at a time
    //      (user + assistant pairs) to maintain role alternation.
    //   c) Record the token count AFTER trimming.
    //   d) Call observeWindow(droppedCount, tokensBefore - tokensAfter)
    // ------------------------------------------------------------------
  }

  addUserMessage(text) {
    /**
     * Add a user message to the conversation history.
     */
    // ------------------------------------------------------------------
    // TODO 4: Push a user message object to this.messages.
    // ------------------------------------------------------------------
  }

  async send() {
    /**
     * Send the conversation to Claude and append the response.
     * Before sending, trim the history to stay within budget.
     * Returns Claude's response text.
     */
    // ------------------------------------------------------------------
    // TODO 5: Call this._trimHistory() first.
    // Then call client.messages.create with:
    //   model: MODEL
    //   max_tokens: 1024
    //   system: this.systemPrompt
    //   messages: this.messages
    // ------------------------------------------------------------------
    let response = null; // Replace with your API call

    // ------------------------------------------------------------------
    // TODO 6: Extract text from response.content and push as assistant
    // message to this.messages.
    // ------------------------------------------------------------------
    let assistantText = "";

    return assistantText;
  }

  getHistory() {
    /**
     * Return the current message history.
     */
    // ------------------------------------------------------------------
    // TODO 7: Return this.messages.
    // ------------------------------------------------------------------
    return [];
  }

  getTokenCount() {
    /**
     * Return estimated token count for current history.
     */
    return this.messages ? this._estimateTokens(this.messages) : 0;
  }
}

// =============================================================================
// MAIN
// =============================================================================

console.log("=".repeat(60));
console.log("M08 Lab - Step 2: Sliding Window Conversation Manager");
console.log("=".repeat(60));

// Use a smaller budget to force window sliding during the test
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
