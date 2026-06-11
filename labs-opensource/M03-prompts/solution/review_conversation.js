/**
 * M03 Lab - Step 3: Multi-Turn Review Conversation — SOLUTION
 * ============================================================
 * Run: node review_conversation.js
 */

import OpenAI from "openai";

class ConversationManager {
  constructor(systemPrompt, model = "mistral") {
    this.client = new OpenAI({ baseURL: "http://localhost:11434/v1", apiKey: "ollama" });
    this.system = systemPrompt;
    this.model = model;
    this.messages = [];
  }

  async send(userMessage) {
    this.messages.push({ role: "user", content: userMessage });

    try {
      const response = await this.client.chat.completions.create({
        model: this.model,
        messages: [{ role: "system", content: this.system }, ...this.messages],
      });
      const assistantText = response.choices[0].message.content;
      this.messages.push({ role: "assistant", content: assistantText });

      return {
        text: assistantText,
        usage: {
          inputTokens: response.usage.prompt_tokens,
          outputTokens: response.usage.completion_tokens,
        },
      };
    } catch (error) {
      this.messages.pop(); // remove failed user message
      throw error;
    }
  }

  getHistory() {
    return [...this.messages];
  }

  clear() {
    this.messages = [];
  }
}

// ── 5-turn review session ──
const REVIEW_SYSTEM_PROMPT = `You are a senior software engineer conducting code reviews.
<role>Review code for correctness, performance, security, and style.</role>
<output_format>Use ## Category headers with bullet points. Be concise.</output_format>
<tone>Be constructive. Praise good patterns.</tone>`;

const conv = new ConversationManager(REVIEW_SYSTEM_PROMPT);
let totalIn = 0;
let totalOut = 0;

const turns = [
  "Review this:\n```python\ndef get_user(id):\n    query = f'SELECT * FROM users WHERE id = {id}'\n    return db.execute(query)\n```",
  "Can you show me the fixed version with parameterized queries?",
  "Now add error handling for the case where the user is not found.",
  "What about connection pooling — is that important here?",
  "Summarize all the improvements we discussed in a checklist.",
];

for (let i = 0; i < turns.length; i++) {
  try {
    const { text, usage } = await conv.send(turns[i]);
    totalIn += usage.inputTokens;
    totalOut += usage.outputTokens;
    console.log(`\n--- Turn ${i + 1} ---`);
    console.log(`You: ${turns[i].slice(0, 60)}...`);
    console.log(`Reviewer: ${text.slice(0, 150)}...`);
    console.log(`This turn: ${usage.inputTokens} in, ${usage.outputTokens} out`);
    console.log(`Cumulative: ${totalIn} in, ${totalOut} out`);
  } catch (error) {
    console.error(`Error on turn ${i + 1}: ${error.message}`);
    break;
  }
}

console.log(`\n${"=".repeat(50)}`);
console.log(`Total: ${conv.getHistory().length} messages, ${totalIn} input + ${totalOut} output tokens`);
