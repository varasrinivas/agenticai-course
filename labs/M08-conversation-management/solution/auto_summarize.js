/**
 * M08 Lab - Step 3: Auto-Summarizing Conversation Manager (Solution)
 * ===================================================================
 * Complete solution: an AutoSummarizeManager that compresses old messages
 * into a summary when the conversation hits 80% of its token budget.
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
// OBSERVATION HELPERS
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
// SOLUTION: AutoSummarizeManager
// =============================================================================

class AutoSummarizeManager {
  constructor(
    systemPrompt = SYSTEM_PROMPT,
    maxTokens = 2048,
    threshold = 0.8
  ) {
    this.systemPrompt = systemPrompt;
    this.maxTokens = maxTokens;
    this.threshold = threshold;
    this.summarizeCount = 0;
    // Step 1: Initialize empty messages array
    this.messages = [];
  }

  _estimateTokens(messages) {
    // Step 2: Estimate tokens
    return Math.floor(
      (this.systemPrompt.length + JSON.stringify(messages).length) / 4
    );
  }

  _shouldSummarize() {
    // Step 3: Check threshold
    return (
      this._estimateTokens(this.messages) >= this.maxTokens * this.threshold
    );
  }

  async _summarizeOldMessages() {
    // Step 4: Calculate split point -- keep the last 1/3 of messages intact
    const splitAt = Math.max(
      2,
      Math.floor((this.messages.length * 2) / 3)
    );
    const oldMessages = this.messages.slice(0, splitAt);
    const recentMessages = this.messages.slice(splitAt);

    // Step 5: Record tokens before summarization
    const tokensBefore = this._estimateTokens(this.messages);

    // Step 6: Build summarization prompt from old messages
    let conversationText = "";
    for (const msg of oldMessages) {
      const role = msg.role.toUpperCase();
      conversationText += `${role}: ${msg.content}\n\n`;
    }

    const summarizePrompt =
      "Summarize this conversation so far in 2-3 sentences. Focus on " +
      "the key topics discussed and any important facts established.\n\n" +
      `Conversation:\n${conversationText}`;

    const summaryResponse = await client.messages.create({
      model: MODEL,
      max_tokens: 256,
      messages: [{ role: "user", content: summarizePrompt }],
    });

    // Step 7: Extract summary text
    let summaryText = "";
    for (const block of summaryResponse.content) {
      if (block.text) {
        summaryText += block.text;
      }
    }

    // Step 8: Build new messages array with summary + recent messages
    const summaryMessage = {
      role: "assistant",
      content: `[Summary of earlier conversation]: ${summaryText}`,
    };

    // Ensure role alternation: if first recent message is also "assistant",
    // insert a bridging user message
    const newMessages = [summaryMessage];
    if (recentMessages.length > 0 && recentMessages[0].role === "assistant") {
      newMessages.push({
        role: "user",
        content: "(continuing conversation)",
      });
    }
    newMessages.push(...recentMessages);

    this.messages = newMessages;

    // Step 9: Record tokens after and log
    const tokensAfter = this._estimateTokens(this.messages);
    this.summarizeCount++;
    observeSummarize(oldMessages.length, tokensBefore, tokensAfter);
    console.log(`[SUMMARIZE] Summary: "${summaryText.slice(0, 100)}..."`);
  }

  addUserMessage(text) {
    // Step 10: Push user message
    this.messages.push({ role: "user", content: text });
  }

  async send() {
    // Step 11: Check if summarization is needed, then call API
    if (this._shouldSummarize()) {
      await this._summarizeOldMessages();
    }

    const response = await client.messages.create({
      model: MODEL,
      max_tokens: 1024,
      system: this.systemPrompt,
      messages: this.messages,
    });

    // Step 12: Extract text and push to history
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
    // Step 13: Return messages
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
console.log(
  "M08 Lab - Step 3: Auto-Summarizing Conversation Manager (SOLUTION)"
);
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
