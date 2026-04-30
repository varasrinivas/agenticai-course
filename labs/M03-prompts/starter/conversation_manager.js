/**
 * M03 Lab — Conversation Manager (Node.js)
 * ==========================================
 * Build a multi-turn conversation manager that maintains
 * full message history across API calls.
 */

import Anthropic from "@anthropic-ai/sdk";
import "dotenv/config";

const client = new Anthropic();
const MODEL = "claude-sonnet-4-6";

class ConversationManager {
  /**
   * Initialize the conversation manager.
   * @param {string} systemPrompt - The system prompt that defines Claude's role.
   */
  constructor(systemPrompt) {
    this.systemPrompt = systemPrompt;
    /** @type {Array<{role: string, content: string}>} */
    this.messages = [];
  }

  /**
   * Send a user message and get Claude's response.
   *
   * This method must:
   * 1. Append the user message to this.messages
   * 2. Call client.messages.create with the full message history
   * 3. Append the assistant response to this.messages
   * 4. Return the response text
   *
   * @param {string} userMessage - The user's message text.
   * @returns {Promise<string>} Claude's response text.
   */
  async send(userMessage) {
    // TODO: Implement the send method.
    //
    // Step 1: Push { role: "user", content: userMessage } to this.messages
    //
    // Step 2: Call client.messages.create with:
    //   - model: MODEL
    //   - max_tokens: 1024
    //   - system: this.systemPrompt
    //   - messages: this.messages  (the FULL history)
    //
    // Step 3: Extract the response text from response.content[0].text
    //
    // Step 4: Push { role: "assistant", content: responseText } to this.messages
    //
    // Step 5: Return the response text
    return "";
  }

  /**
   * Return the full conversation history.
   * @returns {Array<{role: string, content: string}>}
   */
  getHistory() {
    return this.messages;
  }

  /**
   * Clear the conversation history.
   */
  reset() {
    this.messages = [];
  }
}

// ─── Main ───────────────────────────────────────────────────────────────────

const system =
  "You are a UCC filing research assistant. You help users understand " +
  "UCC filings, search for filings, and explain legal terminology in " +
  "plain English. Be concise and accurate.";

const manager = new ConversationManager(system);

const turns = [
  "What is a UCC-1 filing?",
  "How long do they last?",
  "What happens when one expires?",
];

console.log("=".repeat(60));
console.log("Multi-Turn Conversation");
console.log("=".repeat(60));

for (let i = 0; i < turns.length; i++) {
  const userMsg = turns[i];
  console.log(`\n--- Turn ${i + 1} ---`);
  console.log(`USER: ${userMsg}`);
  try {
    const response = await manager.send(userMsg);
    console.log(`CLAUDE: ${response}`);
  } catch (e) {
    console.log(`[ERROR] ${e.message}`);
  }
}

// Show history summary
console.log("\n" + "=".repeat(60));
console.log("Conversation History Summary");
console.log("=".repeat(60));
const history = manager.getHistory();
console.log(`Total messages: ${history.length}`);
for (const msg of history) {
  const role = msg.role.toUpperCase();
  const preview =
    msg.content.length > 80
      ? msg.content.slice(0, 80) + "..."
      : msg.content;
  console.log(`  [${role}] ${preview}`);
}
