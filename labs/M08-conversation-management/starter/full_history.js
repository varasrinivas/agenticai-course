/**
 * M08 Lab - Step 1: Full Conversation History (Starter)
 * =====================================================
 * Build a ConversationManager that stores the entire message history
 * and sends it to Claude on every API call.
 *
 * KEY CONCEPT: Claude is stateless. Every messages.create() call starts
 * from scratch. YOUR code must maintain the conversation history and send
 * it every time. The messages array IS the memory.
 *
 * Usage:
 *     node full_history.js
 */

import Anthropic from "@anthropic-ai/sdk";
import "dotenv/config";

const client = new Anthropic();
const MODEL = "claude-sonnet-4-6";

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

function observeTokens(tokenCount, messageCount) {
  console.log(`[TOKENS] Estimated tokens in conversation: ~${tokenCount}`);
  console.log(`[HISTORY] ${messageCount} messages in history`);
}

// =============================================================================
// YOUR CODE: Implement ConversationManager
// =============================================================================

class ConversationManager {
  /**
   * Manages a multi-turn conversation with Claude by maintaining full history.
   *
   * The messages list grows with every turn. Every API call sends the
   * complete history so Claude has full context.
   */

  constructor(systemPrompt = SYSTEM_PROMPT) {
    this.systemPrompt = systemPrompt;
    // ------------------------------------------------------------------
    // TODO 1: Initialize an empty array to store messages.
    // Each message is an object: { role: "user"|"assistant", content: "..." }
    // ------------------------------------------------------------------
    this.messages = null; // Replace with correct initialization
  }

  addUserMessage(text) {
    /**
     * Add a user message to the conversation history.
     */
    // ------------------------------------------------------------------
    // TODO 2: Push a user message object to this.messages.
    // Format: { role: "user", content: text }
    // ------------------------------------------------------------------
  }

  async send() {
    /**
     * Send the current conversation to Claude and append the response.
     * Returns Claude's response text.
     */
    // ------------------------------------------------------------------
    // TODO 3: Call client.messages.create with:
    //   model: MODEL
    //   max_tokens: 1024
    //   system: this.systemPrompt
    //   messages: this.messages
    // ------------------------------------------------------------------
    let response = null; // Replace with your API call

    // ------------------------------------------------------------------
    // TODO 4: Extract the text from response.content.
    // Loop through response.content blocks, collect text from blocks
    // that have a .text property.
    // ------------------------------------------------------------------
    let assistantText = "";

    // ------------------------------------------------------------------
    // TODO 5: Push the assistant's response to this.messages.
    // Format: { role: "assistant", content: assistantText }
    // ------------------------------------------------------------------

    return assistantText;
  }

  getHistory() {
    /**
     * Return the full message history.
     */
    // ------------------------------------------------------------------
    // TODO 6: Return the messages array.
    // ------------------------------------------------------------------
    return [];
  }

  getTokenCount() {
    /**
     * Estimate the token count for the current conversation.
     * Uses a simple heuristic: Math.floor(str.length / 4)
     */
    // ------------------------------------------------------------------
    // TODO 7: Estimate tokens using:
    //   Math.floor(JSON.stringify(this.messages).length / 4)
    // Include the system prompt in the estimate.
    // ------------------------------------------------------------------
    return 0;
  }
}

// =============================================================================
// MAIN
// =============================================================================

console.log("=".repeat(60));
console.log("M08 Lab - Step 1: Full Conversation History");
console.log("=".repeat(60));

const manager = new ConversationManager();

const testQuestions = [
  "What is a UCC-1 filing?",
  "How long does a UCC-1 last before it lapses?",
  "What happens when a filing lapses?",
  "Can a filing be renewed?",
  "Summarize everything we discussed",
];

for (let i = 0; i < testQuestions.length; i++) {
  const question = testQuestions[i];
  console.log(`\n--- Turn ${i + 1}/${testQuestions.length} ---`);

  observe("USER", question);
  manager.addUserMessage(question);
  observeTokens(manager.getTokenCount(), manager.getHistory().length);

  const response = await manager.send();

  observe("ASSISTANT", response);
  observeTokens(manager.getTokenCount(), manager.getHistory().length);
}

console.log(`\n${"=".repeat(60)}`);
console.log(
  `Final conversation: ${manager.getHistory().length} messages, ` +
    `~${manager.getTokenCount()} estimated tokens`
);
console.log("=".repeat(60));
