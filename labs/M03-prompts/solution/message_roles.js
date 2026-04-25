/**
 * M03 Lab — Message Roles (Node.js Solution)
 * =============================================
 * Explore how system prompts, user messages, and assistant prefill
 * change Claude's responses to the same question.
 */

import Anthropic from "@anthropic-ai/sdk";
import "dotenv/config";

const client = new Anthropic();
const MODEL = "claude-sonnet-4-20250514";

/**
 * Send a simple user message with no system prompt.
 * @param {string} userMessage
 * @returns {Promise<string>}
 */
async function basicCall(userMessage) {
  const response = await client.messages.create({
    model: MODEL,
    max_tokens: 1024,
    messages: [{ role: "user", content: userMessage }],
  });
  return response.content[0].text;
}

/**
 * Send a user message with a system prompt that sets Claude's role.
 * @param {string} system
 * @param {string} userMessage
 * @returns {Promise<string>}
 */
async function withSystemPrompt(system, userMessage) {
  const response = await client.messages.create({
    model: MODEL,
    max_tokens: 1024,
    system,
    messages: [{ role: "user", content: userMessage }],
  });
  return response.content[0].text;
}

/**
 * Use assistant prefill to guide the response format.
 * @param {string} system
 * @param {string} userMessage
 * @param {string} assistantPrefill
 * @returns {Promise<string>}
 */
async function withPrefill(system, userMessage, assistantPrefill) {
  const response = await client.messages.create({
    model: MODEL,
    max_tokens: 1024,
    system,
    messages: [
      { role: "user", content: userMessage },
      { role: "assistant", content: assistantPrefill },
    ],
  });
  return assistantPrefill + response.content[0].text;
}

// ─── Main ───────────────────────────────────────────────────────────────────

const question = "What is a UCC-1 filing?";

const systemPrompt =
  "You are a UCC filing expert. You specialize in Uniform Commercial Code " +
  "filings, secured transactions, and lien searches. Provide accurate, " +
  "concise explanations using proper legal terminology while remaining " +
  "accessible to non-lawyers.";

const prefill = "## Analysis\n";

// --- Call 1: Basic (no system prompt) ---
console.log("=".repeat(60));
console.log("CALL 1: Basic — No System Prompt");
console.log("=".repeat(60));
try {
  const result = await basicCall(question);
  console.log(result);
} catch (e) {
  console.log(`[ERROR] ${e.message}`);
}

// --- Call 2: With system prompt ---
console.log("\n" + "=".repeat(60));
console.log("CALL 2: With System Prompt (UCC Expert)");
console.log("=".repeat(60));
try {
  const result = await withSystemPrompt(systemPrompt, question);
  console.log(result);
} catch (e) {
  console.log(`[ERROR] ${e.message}`);
}

// --- Call 3: With system prompt + prefill ---
console.log("\n" + "=".repeat(60));
console.log("CALL 3: With System Prompt + Assistant Prefill");
console.log("=".repeat(60));
try {
  const result = await withPrefill(systemPrompt, question, prefill);
  console.log(result);
} catch (e) {
  console.log(`[ERROR] ${e.message}`);
}
