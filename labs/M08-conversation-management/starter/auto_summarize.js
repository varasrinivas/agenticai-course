/**
 * M08 Lab - Step 3: Auto-Summarizing Conversation Manager (Starter)
 * ==================================================================
 * Build an AutoSummarizeManager that compresses old messages into a
 * summary when the conversation hits 80% of its token budget.
 *
 * KEY CONCEPT: Sliding windows lose information forever. Summarization
 * preserves the GIST of old messages in fewer tokens, so Claude retains
 * awareness of earlier topics even after compression.
 *
 * Usage:
 *     node auto_summarize.js
 */

import Anthropic from "@anthropic-ai/sdk";
import "dotenv/config";

const client = new Anthropic();
const MODEL = "claude-sonnet-4-20250514";

const SYSTEM_PROMPT =
  "You are a UCC filing research assistant. Help users understand " +
  "UCC filings, lien risks, and secured transactions. Provide clear, " +
  "concise answers. When referencing prior conversation, demonstrate " +
  "you remember the context.";

// =============================================================================
// OBSERVATION HELPERS (complete -- do not modify)
// =============================================================================

function observe(label, message) {
  console.log(`\n${"=".repeat(60)}`);
  console.log(`[${label}] ${message}`);
  console.log("=".repeat(60));
}

function observeTokens(tokenCount, maxTokens, messageCount) {
  const pct = maxTokens > 0 ? (tokenCount / maxTokens) * 100 : 0;
  const marker = pct >= 80 ? " *** ABOVE 80% THRESHOLD ***" : "";
  console.log(
    `[TOKENS] ~${tokenCount} / ${maxTokens} (${Math.round(pct)}%)${marker}`
  );
  console.log(`[HISTORY] ${messageCount} messages in history`);
}

function observeSummarize(numMessages, tokensBefore, tokensAfter) {
  console.log(
    `[SUMMARIZE] Compressed ${numMessages} messages into summary ` +
      `(${tokensBefore} tokens -> ${tokensAfter} tokens)`
  );
}

// =============================================================================
// YOUR CODE: Implement AutoSummarizeManager
// =============================================================================

class AutoSummarizeManager {
  /**
   * Manages conversation history with automatic summarization.
   *
   * When the conversation reaches 80% of the token budget, the oldest
   * messages are sent to Claude for summarization. The summary replaces
   * those messages, dramatically reducing token usage while preserving
   * context.
   */

  constructor(
    systemPrompt = SYSTEM_PROMPT,
    maxTokens = 2048,
    threshold = 0.8
  ) {
    this.systemPrompt = systemPrompt;
    this.maxTokens = maxTokens;
    this.threshold = threshold;
    this.summarizeCount = 0;
    // ------------------------------------------------------------------
    // TODO 1: Initialize an empty array to store messages.
    // ------------------------------------------------------------------
    this.messages = null; // Replace with correct initialization
  }

  _estimateTokens(messages) {
    /**
     * Estimate token count for a list of messages plus system prompt.
     */
    // ------------------------------------------------------------------
    // TODO 2: Estimate tokens using:
    //   Math.floor((this.systemPrompt.length + JSON.stringify(messages).length) / 4)
    // ------------------------------------------------------------------
    return 0;
  }

  _shouldSummarize() {
    /**
     * Check if current token usage exceeds the threshold.
     * Returns true if tokens >= maxTokens * threshold.
     */
    // ------------------------------------------------------------------
    // TODO 3: Return true if _estimateTokens >= maxTokens * threshold
    // ------------------------------------------------------------------
    return false;
  }

  async _summarizeOldMessages() {
    /**
     * Compress old messages into a summary.
     *
     * Steps:
     * 1. Split messages into "old" (first 2/3) and "recent" (last 1/3).
     * 2. Send old messages to Claude asking for a 2-3 sentence summary.
     * 3. Create a summary message with role "assistant".
     * 4. Replace this.messages with [summaryMessage, ...recentMessages].
     * 5. Log the compression with observeSummarize.
     */
    // ------------------------------------------------------------------
    // TODO 4: Calculate the split point.
    //   const splitAt = Math.max(2, Math.floor((this.messages.length * 2) / 3));
    //   const oldMessages = this.messages.slice(0, splitAt);
    //   const recentMessages = this.messages.slice(splitAt);
    // ------------------------------------------------------------------

    // ------------------------------------------------------------------
    // TODO 5: Record tokens BEFORE summarization.
    //   const tokensBefore = this._estimateTokens(this.messages);
    // ------------------------------------------------------------------

    // ------------------------------------------------------------------
    // TODO 6: Build a summarization prompt.
    //   Format old messages as readable text, then ask Claude:
    //   "Summarize this conversation so far in 2-3 sentences. Focus on
    //    the key topics discussed and any important facts established."
    //
    //   Call client.messages.create with:
    //     model: MODEL
    //     max_tokens: 256
    //     messages: [{ role: "user", content: summarizePrompt }]
    // ------------------------------------------------------------------

    // ------------------------------------------------------------------
    // TODO 7: Extract the summary text from the response.
    // ------------------------------------------------------------------
    let summaryText = "";

    // ------------------------------------------------------------------
    // TODO 8: Build new messages array:
    //   const summaryMessage = {
    //     role: "assistant",
    //     content: `[Summary of earlier conversation]: ${summaryText}`
    //   };
    //   this.messages = [summaryMessage, ...recentMessages];
    //
    //   BUT: ensure role alternation! If the first recent message is also
    //   "assistant", insert a bridging user message:
    //   { role: "user", content: "(continuing conversation)" }
    // ------------------------------------------------------------------

    // ------------------------------------------------------------------
    // TODO 9: Record tokens AFTER summarization and log.
    //   const tokensAfter = this._estimateTokens(this.messages);
    //   this.summarizeCount++;
    //   observeSummarize(oldMessages.length, tokensBefore, tokensAfter);
    //   console.log(`[SUMMARIZE] Summary: "${summaryText.slice(0, 100)}..."`);
    // ------------------------------------------------------------------
  }

  addUserMessage(text) {
    /**
     * Add a user message to the conversation history.
     */
    // ------------------------------------------------------------------
    // TODO 10: Push a user message object to this.messages.
    // ------------------------------------------------------------------
  }

  async send() {
    /**
     * Send the conversation to Claude and append the response.
     * Before sending, check if summarization is needed.
     * Returns Claude's response text.
     */
    // ------------------------------------------------------------------
    // TODO 11: Check _shouldSummarize() and call _summarizeOldMessages()
    // if needed. Then call client.messages.create with:
    //   model: MODEL
    //   max_tokens: 1024
    //   system: this.systemPrompt
    //   messages: this.messages
    // ------------------------------------------------------------------
    let response = null; // Replace with your API call

    // ------------------------------------------------------------------
    // TODO 12: Extract text from response.content and push as assistant
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
    // TODO 13: Return this.messages.
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
console.log("M08 Lab - Step 3: Auto-Summarizing Conversation Manager");
console.log("=".repeat(60));

const manager = new AutoSummarizeManager(SYSTEM_PROMPT, 2048);
const thresholdTokens = Math.floor(manager.maxTokens * manager.threshold);
console.log(
  `Token budget: ${manager.maxTokens} tokens ` +
    `(summarize at 80% = ${thresholdTokens} tokens)`
);

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
  "How do fixture filings work?",
  "What is a debtor-in-possession?",
  "What is the difference between attachment and perfection?",
  "Give me a final summary of everything we covered",
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
  `Final: ${manager.getHistory().length} messages, ` +
    `${manager.summarizeCount} summarization events triggered`
);
console.log("=".repeat(60));
