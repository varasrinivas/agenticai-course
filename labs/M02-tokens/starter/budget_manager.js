/**
 * M02 Lab — Step 3: Context Window Budget Manager (Node.js)
 * ===========================================================
 * Track token usage across a conversation and trim when needed.
 */

class ContextBudgetManager {
  /**
   * @param {number} maxTokens - Maximum token budget for the context window
   */
  constructor(maxTokens = 1000) {
    this.maxTokens = maxTokens;
    /** @type {Array<{role: string, content: string, tokens: number}>} */
    this.messages = [];
    this.totalTokens = 0;
  }

  /**
   * Approximate token count for a string.
   * Splits on whitespace and punctuation boundaries.
   * @param {string} text
   * @returns {number}
   */
  _countTokens(text) {
    // Simple approximation: ~4 characters per token for English text
    return Math.ceil(text.length / 4);
  }

  /**
   * Add a message and return token info.
   * @param {string} role - "user" or "assistant"
   * @param {string} content - Message text
   * @returns {{ tokens: number, total: number, max: number }}
   */
  addMessage(role, content) {
    // TODO:
    // 1. Count tokens in the content using this._countTokens()
    // 2. Push { role, content, tokens: tokenCount } to this.messages
    // 3. Add the token count to this.totalTokens
    // 4. Return { tokens: tokenCount, total: this.totalTokens, max: this.maxTokens }
    return null;
  }

  /**
   * Return current token usage stats.
   * @returns {{ used: number, max: number, remaining: number, percent: number }}
   */
  getUsage() {
    // TODO: Return { used: this.totalTokens, max: this.maxTokens,
    //               remaining: this.maxTokens - this.totalTokens,
    //               percent: (this.totalTokens / this.maxTokens) * 100 }
    return null;
  }

  /**
   * Check if new text would fit in remaining budget.
   * @param {string} text
   * @returns {boolean}
   */
  wouldFit(text) {
    // TODO: Count tokens in text and check if total + new <= max
    return false;
  }

  /**
   * Remove oldest messages until under budget.
   * @returns {number} Count of messages removed
   */
  trimOldest() {
    // TODO:
    // 1. Initialize a removed counter to 0
    // 2. While this.totalTokens > this.maxTokens and this.messages.length > 0:
    //    - Shift the first (oldest) message from this.messages
    //    - Subtract its tokens from this.totalTokens
    //    - Increment removed
    // 3. Return removed
    return 0;
  }
}

// ─── Main ───────────────────────────────────────────────────────────────────

console.log("=== Context Window Budget Manager ===\n");
const mgr = new ContextBudgetManager(1000);

console.log("Adding messages to conversation...");
const sampleMessages = [
  [
    "user",
    "What is machine learning?",
  ],
  [
    "assistant",
    "Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed. It focuses on developing algorithms that can access data, learn from it, and make predictions or decisions.",
  ],
  ["user", "Can you give me an example?"],
  [
    "assistant",
    "Sure! Consider email spam filtering. A machine learning model is trained on thousands of emails labeled as spam or not-spam. It learns patterns like certain keywords, sender addresses, or formatting tricks that indicate spam. When a new email arrives, the model uses these learned patterns to predict whether it's spam, without anyone having to write explicit rules for every possible spam message.",
  ],
];

for (let i = 0; i < sampleMessages.length; i++) {
  const [role, content] = sampleMessages[i];
  try {
    const info = mgr.addMessage(role, content);
    const preview =
      content.length > 40 ? content.slice(0, 40) + "..." : content;
    console.log(
      `  [${i + 1}] ${role}: "${preview}" — ${info.tokens} tokens (${info.total} / ${info.max} used)`
    );
  } catch (e) {
    console.log(`  [${i + 1}] [ERROR] ${e.message}`);
  }
}

console.log();
try {
  const usage = mgr.getUsage();
  console.log(
    `Current usage: ${usage.used} / ${usage.max} tokens (${usage.percent.toFixed(1)}%)`
  );
  console.log(`Remaining: ${usage.remaining} tokens`);
} catch (e) {
  console.log(`[ERROR] ${e.message}`);
}

console.log();
console.log(`Would a 500-token message fit? ${mgr.wouldFit("x ".repeat(250))}`);
console.log(`Would a 900-token message fit? ${mgr.wouldFit("x ".repeat(450))}`);

console.log("\nSimulating context overflow...");
console.log("  Adding 5 large messages (200 tokens each)...");
for (let i = 0; i < 5; i++) {
  mgr.addMessage("user", "This is a large padding message. ".repeat(30));
}

try {
  const usage = mgr.getUsage();
  const status = usage.used > usage.max ? "OVER BUDGET" : "OK";
  console.log(
    `  Usage before trim: ${usage.used} / ${usage.max} tokens (${usage.percent.toFixed(1)}%) — ${status}`
  );
  const removed = mgr.trimOldest();
  const usageAfter = mgr.getUsage();
  console.log("  Trimming oldest messages...");
  console.log(
    `  Usage after trim: ${usageAfter.used} / ${usageAfter.max} tokens (${usageAfter.percent.toFixed(1)}%)`
  );
  console.log(`  Removed ${removed} messages to get back under budget.`);
} catch (e) {
  console.log(`  [ERROR] ${e.message}`);
}
