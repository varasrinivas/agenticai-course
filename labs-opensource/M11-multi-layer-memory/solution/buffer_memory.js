/**
 * M11 Lab - Step 1: BufferMemory — SOLUTION
 * ==========================================
 * Run: node buffer_memory.js
 */

import { pathToFileURL } from "node:url";

export class BufferMemory {
  constructor({ maxMessages = 20, maxTokens = 4000 } = {}) {
    this.messages = [];
    this.maxMessages = maxMessages;
    this.maxTokens = maxTokens;
  }

  /** 4-chars-per-token heuristic — good enough for eviction. */
  _estimateTokens(messages) {
    const totalChars = messages.reduce(
      (s, m) => s + String(m.content ?? "").length + (m.role ?? "").length,
      0
    );
    return Math.floor(totalChars / 4);
  }

  tokenCount() {
    return this._estimateTokens(this.messages);
  }

  add(role, content) {
    this.messages.push({ role, content });

    // Evict by count — always in user+assistant PAIRS
    while (this.messages.length > this.maxMessages) {
      this.messages.shift();
      if (this.messages.length) this.messages.shift();
    }

    // Evict by tokens — pairs again
    if (this.maxTokens != null) {
      while (this.messages.length >= 2 && this._estimateTokens(this.messages) > this.maxTokens) {
        this.messages.shift();
        this.messages.shift();
      }
    }
  }

  get() {
    return [...this.messages];
  }

  clear() {
    this.messages = [];
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const buf = new BufferMemory({ maxMessages: 6, maxTokens: 200 });

  for (let i = 0; i < 5; i++) {
    buf.add("user", `Query number ${i}: what is the status of order ${i}?`);
    buf.add("assistant", `Order ${i} is shipped. Tracking: TRK${String(i).padStart(4, "0")}.`);
  }

  console.log(`BufferMemory(messages=${buf.get().length}, ~${buf.tokenCount()} tokens)`);
  for (const m of buf.get()) console.log(`  [${m.role}] ${m.content.slice(0, 60)}`);

  console.assert(buf.get().length <= 6, "max_messages eviction failed");
  console.assert(buf.tokenCount() <= 200, "token eviction failed");
  console.assert(buf.get()[0]?.role === "user", "buffer must start with a user turn (evict in pairs!)");
  console.log("\nAll eviction checks passed.");
}
