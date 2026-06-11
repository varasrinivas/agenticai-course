/**
 * M02 Lab - Step 3: TokenTimer Benchmark — SOLUTION
 * ==================================================
 * Run: node token_timer.js
 */

import OpenAI from "openai";

class TokenTimer {
  constructor(model = "mistral") {
    this.model = model;
    this.client = new OpenAI({ baseURL: "http://localhost:11434/v1", apiKey: "ollama" });
  }

  async run(messages, maxTokens = 256) {
    const tStart = performance.now();
    let response;
    try {
      response = await this.client.chat.completions.create({
        model: this.model,
        messages,
        max_tokens: maxTokens,
      });
    } catch (err) {
      throw new Error(`Ollama request failed: ${err.message} (is Ollama running? ollama serve)`);
    }

    const elapsed = (performance.now() - tStart) / 1000; // seconds
    const usage = response.usage;
    const content = response.choices[0].message.content ?? "";
    const decodeTps = elapsed > 0 ? usage.completion_tokens / elapsed : 0;

    return {
      promptTokens: usage.prompt_tokens,
      completionTokens: usage.completion_tokens,
      totalTokens: usage.total_tokens,
      elapsedSeconds: elapsed,
      decodeTokensPerSec: decodeTps,
      content,
    };
  }
}

// ── Benchmark over three prompt sizes ──
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
