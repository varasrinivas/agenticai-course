/**
 * M03B Lab: The ContextBudget Class — SOLUTION
 * =============================================
 * Run the full lab: copy this over starter/context_budget.js, then node diagnose.js
 */

import { getEncoding } from "js-tiktoken";
import OpenAI from "openai";

// cl100k_base is OpenAI's tokenizer — a good approximation for Mistral/Llama
const enc = getEncoding("cl100k_base");

/** Count tokens in a string or JSON-serializable object. */
export function countTokens(text) {
  const s = typeof text === "string" ? text : JSON.stringify(text);
  return Math.max(1, enc.encode(s).length);
}

export const MODEL_LIMITS = {
  mistral: 32_768,
  mixtral: 32_768,
  llama3: 131_072,
  gemma2: 8_192,
};

const SUMMARY_PROMPT = `Summarize this conversation in 3-5 sentences.
CRITICAL: preserve every order ID, customer ID, tracking number, exact dollar amount,
and explicit user decision. Drop only retry errors, duplicate results, and resolved detours.

Conversation:
{transcript}

Summary:`;

/**
 * Summarize older turns; keep the last `keepRecent` turns verbatim.
 * GOTCHA: this is a SEPARATE model call — never ask the main model to
 * summarize the context it is currently reading.
 */
export async function summarizeHistory(history, keepRecent = 4) {
  if (history.length <= keepRecent) return history;

  const older = history.slice(0, -keepRecent);
  const recent = history.slice(-keepRecent);
  const transcript = older.map((m) => `${m.role}: ${m.content}`).join("\n");

  const client = new OpenAI({ baseURL: "http://localhost:11434/v1", apiKey: "ollama" });
  try {
    const result = await client.chat.completions.create({
      model: "mistral",
      messages: [{ role: "user", content: SUMMARY_PROMPT.replace("{transcript}", transcript) }],
      max_tokens: 250,
    });
    const summaryText = result.choices[0].message.content ?? "";
    return [
      { role: "user", content: `[Summary of ${older.length} earlier turns] ${summaryText}` },
      ...recent,
    ];
  } catch (e) {
    console.error(`Summarization failed: ${e.message}; falling back to truncation.`);
    return recent;
  }
}

export class ContextBudget {
  constructor(opts = {}) {
    this.systemPrompt = opts.systemPrompt ?? "";
    this.toolDefinitions = opts.toolDefinitions ?? [];
    this.retrievedDocs = opts.retrievedDocs ?? [];
    this.history = opts.history ?? [];
    this.toolResults = opts.toolResults ?? [];
    this.currentUserMessage = opts.currentUserMessage ?? "";
    this.model = opts.model ?? "mistral";
    this.reserveOutput = opts.reserveOutput ?? 2048;
  }

  get maxTokens() {
    return (MODEL_LIMITS[this.model] ?? 32_768) - this.reserveOutput;
  }

  /** Per-layer token breakdown. */
  account() {
    return {
      system: countTokens(this.systemPrompt),
      tools: this.toolDefinitions.length ? countTokens(this.toolDefinitions) : 0,
      retrieved: this.retrievedDocs.reduce((s, d) => s + countTokens(d), 0),
      history: this.history.reduce((s, m) => s + countTokens(m.content), 0),
      toolResults: this.toolResults.reduce((s, r) => s + countTokens(r), 0),
      current: countTokens(this.currentUserMessage),
    };
  }

  total() {
    return Object.values(this.account()).reduce((a, b) => a + b, 0);
  }

  remaining() {
    return this.maxTokens - this.total();
  }

  fits() {
    return this.total() <= this.maxTokens;
  }

  /** Return recommended strategy based on budget utilization. */
  strategy() {
    const utilization = this.total() / this.maxTokens;
    if (utilization < 0.60) return "ok";        // plenty of room
    if (utilization < 0.75) return "compress";  // crop tool defs, compress results
    if (utilization < 0.90) return "summarize"; // summarize old history turns
    return "critical";                          // system + last 2 turns + current only
  }

  /** Apply the recommended strategy in place. Returns this for chaining. */
  crop() {
    const strat = this.strategy();
    if (strat === "ok") return this;

    if (["compress", "summarize", "critical"].includes(strat)) {
      // Crop tool definitions when in trouble (saves ~900 tok for 4 tools)
      this.toolDefinitions = [];
    }

    if (["summarize", "critical"].includes(strat)) {
      const keep = strat === "critical" ? 2 : 4;
      this.history = this.history.slice(-keep);
      this.toolResults = this.toolResults.slice(-2);
    }

    if (strat === "critical") {
      // Nuclear option: drop all retrieved docs too
      this.retrievedDocs = [];
    }

    return this;
  }

  /** Summarize old history turns. Call when strategy() === "summarize". */
  async checkpoint(keepRecent = 4) {
    this.history = await summarizeHistory(this.history, keepRecent);
    return this;
  }

  /**
   * Assemble { system, messages } for client.chat.completions.create().
   * Retrieved docs are appended to the CURRENT message, not the system
   * prompt — end position = maximum recall on Mistral-7B.
   */
  buildMessages() {
    let retrievedBlock = "";
    if (this.retrievedDocs.length) {
      retrievedBlock =
        "\n\n<reference_docs>\n" + this.retrievedDocs.join("\n---\n") + "\n</reference_docs>\n\n";
    }

    const messages = [
      ...this.history,
      { role: "user", content: retrievedBlock + this.currentUserMessage },
    ];
    return { system: this.systemPrompt, messages };
  }
}
