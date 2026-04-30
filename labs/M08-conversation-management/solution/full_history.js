/**
 * M08 Lab - Step 1: Full Conversation History (Solution)
 * ======================================================
 * Complete solution: a ConversationManager that stores the entire message
 * history and sends it to Claude on every API call.
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
// OBSERVATION HELPERS
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
// SOLUTION: ConversationManager
// =============================================================================

class ConversationManager {
  constructor(systemPrompt = SYSTEM_PROMPT) {
    this.systemPrompt = systemPrompt;
    // Step 1: Initialize empty messages array
    this.messages = [];
  }

  addUserMessage(text) {
    // Step 2: Push user message
    this.messages.push({ role: "user", content: text });
  }

  async send() {
    // Step 3: Call the API with full history
    const response = await client.messages.create({
      model: MODEL,
      max_tokens: 1024,
      system: this.systemPrompt,
      messages: this.messages,
    });

    // Step 4: Extract text from response
    let assistantText = "";
    for (const block of response.content) {
      if (block.text) {
        assistantText += block.text;
      }
    }

    // Step 5: Push assistant response to history
    this.messages.push({ role: "assistant", content: assistantText });

    return assistantText;
  }

  getHistory() {
    // Step 6: Return messages
    return this.messages;
  }

  getTokenCount() {
    // Step 7: Estimate tokens (system prompt + messages)
    const totalChars =
      this.systemPrompt.length + JSON.stringify(this.messages).length;
    return Math.floor(totalChars / 4);
  }
}

// =============================================================================
// MAIN
// =============================================================================

console.log("=".repeat(60));
console.log("M08 Lab - Step 1: Full Conversation History (SOLUTION)");
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
