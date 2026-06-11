/**
 * M02 Lab - Step 3: TokenTimer Benchmark
 * =======================================
 * Measure your machine's real tokens-per-second with local Mistral.
 * Run: node token_timer.js
 */

import OpenAI from "openai";

class TokenTimer {
  constructor(model = "mistral") {
    this.model = model;
    this.client = new OpenAI({ baseURL: "http://localhost:11434/v1", apiKey: "ollama" });
  }

  /**
   * Send a chat request and return timing metrics.
   *
   * TODO:
   * 1. const tStart = performance.now();
   * 2. await this.client.chat.completions.create({ model: this.model,
   *      messages, max_tokens: maxTokens })
   *    — wrap in try/catch and throw a helpful Error on failure
   * 3. const elapsed = (performance.now() - tStart) / 1000;  // seconds
   * 4. const usage = response.usage; const content = ...message.content ?? "";
   * 5. decodeTps = usage.completion_tokens / elapsed (guard against elapsed === 0)
   * 6. Return { promptTokens, completionTokens, totalTokens,
   *             elapsedSeconds, decodeTokensPerSec, content }
   */
  async run(messages, maxTokens = 256) {
    // TODO: implement
  }
}

// ── Benchmark over three prompt sizes (COMPLETE) ──
function makePrompt(approxTokens) {
  const padding = "benchmark ".repeat(Math.floor(approxTokens / 2));
  return [
    { role: "system", content: "You are a helpful assistant. Answer briefly." },
    { role: "user", content: `Please summarize the following:\n\n${padding}\n\nSummarize in one sentence.` },
  ];
}

const timer = new TokenTimer("mistral");

console.log("Warming up...");
await timer.run([{ role: "user", content: "hi" }], 5);

console.log("\nBenchmark results:");
console.log(
  `${"Approx Input".padStart(14)} ${"Prompt Tok".padStart(10)} ${"Comp Tok".padStart(9)} ${"Elapsed".padStart(8)} ${"Decode tok/s".padStart(13)}`
);
console.log("-".repeat(60));

for (const target of [100, 500, 1_000]) {
  const msgs = makePrompt(target);
  const r = await timer.run(msgs, 64);
  console.log(
    `${(target + "->").padStart(14)} ` +
    `${String(r.promptTokens).padStart(9)} ` +
    `${String(r.completionTokens).padStart(9)} ` +
    `${r.elapsedSeconds.toFixed(2).padStart(7)}s ` +
    `${r.decodeTokensPerSec.toFixed(1).padStart(12)}`
  );
}
