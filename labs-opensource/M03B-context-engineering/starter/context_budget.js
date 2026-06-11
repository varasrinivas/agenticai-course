/**
 * M03B Lab: The ContextBudget Class
 * ==================================
 * Accounts for and curates the six layers of a local-model context.
 * You implement: account(), strategy(), crop(), buildMessages().
 * Provided complete: countTokens, MODEL_LIMITS, summarizeHistory, checkpoint().
 */

import { getEncoding } from "js-tiktoken";
import OpenAI from "openai";

// cl100k_base is OpenAI's tokenizer — a good approximation for Mistral/Llama
const enc = getEncoding("cl100k_base");

/** Count tokens in a string or JSON-serializable object. (COMPLETE) */
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
 * Summarize older turns; keep the last `keepRecent` turns verbatim. (COMPLETE)
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
      model: "mistral", // use a fast/cheap local model for summarization
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
    return recent; // safe fallback: just keep recent turns
  }
}

export class ContextBudget {
  constructor(opts = {}) {
    this.systemPrompt = opts.systemPrompt ?? "";
    this.toolDefinitions = opts.toolDefinitions ?? [];
    this.retrievedDocs = opts.retrievedDocs ?? [];      // semi-static
    this.history = opts.history ?? [];                  // [{role, content}]
    this.toolResults = opts.toolResults ?? [];
    this.currentUserMessage = opts.currentUserMessage ?? "";
    this.model = opts.model ?? "mistral";
    this.reserveOutput = opts.reserveOutput ?? 2048;    // reserved for the reply
  }

  get maxTokens() {
    return (MODEL_LIMITS[this.model] ?? 32_768) - this.reserveOutput;
  }

  /**
   * Per-layer token breakdown.
   * TODO: return an object with these keys (use countTokens):
   *   system      — tokens in this.systemPrompt
   *   tools       — countTokens(this.toolDefinitions) if any, else 0
   *   retrieved   — sum over this.retrievedDocs
   *   history     — sum of countTokens(m.content) over this.history
   *   toolResults — sum over this.toolResults
   *   current     — tokens in this.currentUserMessage
   */
  account() {
    // TODO: implement
  }

  /** (COMPLETE once account() works) */
  total() {
    return Object.values(this.account()).reduce((a, b) => a + b, 0);
  }

  remaining() {
    return this.maxTokens - this.total();
  }

  fits() {
    return this.total() <= this.maxTokens;
  }

  /**
   * Return recommended strategy based on budget utilization.
   * TODO: const utilization = this.total() / this.maxTokens;
   *   < 0.60 → "ok"          (plenty of room)
   *   < 0.75 → "compress"    (crop tool defs, compress tool results)
   *   < 0.90 → "summarize"   (summarize old history turns)
   *   else   → "critical"    (keep only system + last 2 turns + current)
   */
  strategy() {
    // TODO: implement
  }

  /**
   * Apply the recommended strategy in place. Returns this for chaining.
   * TODO:
   * - const strat = this.strategy(); if "ok", return this unchanged
   * - For "compress"/"summarize"/"critical": this.toolDefinitions = []
   *   (saves ~900 tokens for 4 tools)
   * - For "summarize"/"critical": keep only the last 4 history turns
   *   (2 if critical) and the last 2 toolResults
   * - For "critical" only: also drop all retrievedDocs
   * - Return this
   */
  crop() {
    // TODO: implement
  }

  /** Summarize old history turns. Call when strategy() === "summarize". (COMPLETE) */
  async checkpoint(keepRecent = 4) {
    this.history = await summarizeHistory(this.history, keepRecent);
    return this;
  }

  /**
   * Assemble { system, messages } for client.chat.completions.create().
   *
   * Order: system (start, high recall) → history → retrieved docs +
   * current message (end, high recall). Never bury key facts in the middle.
   *
   * TODO:
   * - If this.retrievedDocs is non-empty, build:
   *     "\n\n<reference_docs>\n" + docs.join("\n---\n") + "\n</reference_docs>\n\n"
   *   (appended to the CURRENT user message — end position = max recall on Mistral-7B)
   * - const messages = [...this.history, { role: "user",
   *     content: retrievedBlock + this.currentUserMessage }];
   * - Return { system: this.systemPrompt, messages };
   */
  buildMessages() {
    // TODO: implement
  }
}
