/**
 * M11 Lab - Step 1: BufferMemory (Layer 1 — this session)
 * ========================================================
 * Sliding window buffer with token-aware eviction.
 * Run: node buffer_memory.js
 */

import { pathToFileURL } from "node:url";
import assert from "node:assert/strict";

export class BufferMemory {
  constructor({ maxMessages = 20, maxTokens = 4000 } = {}) {
    this.messages = [];
    this.maxMessages = maxMessages;
    this.maxTokens = maxTokens;
  }

  /** (COMPLETE) 4-chars-per-token heuristic — good enough for eviction. */
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

  /**
   * Add a message and evict oldest messages if over limits.
   *
   * TODO:
   * 1. Push { role, content }
   * 2. While this.messages.length > this.maxMessages:
   *      shift() TWICE — always evict in user+assistant PAIRS;
   *      an orphaned turn confuses the model
   * 3. If this.maxTokens != null:
   *      while this.messages.length >= 2 &&
   *            this._estimateTokens(this.messages) > this.maxTokens:
   *        shift() twice (pairs again)
   */
  add(role, content) {
    // TODO: implement
  }

  /** (COMPLETE) Safe to pass directly to the API. */
  get() {
    return [...this.messages];
  }

  clear() {
    this.messages = [];
  }
}

// ── Smoke test (COMPLETE) ──
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const buf = new BufferMemory({ maxMessages: 6, maxTokens: 200 });

  for (let i = 0; i < 5; i++) {
    buf.add("user", `Query number ${i}: what is the status of order ${i}?`);
    buf.add("assistant", `Order ${i} is shipped. Tracking: TRK${String(i).padStart(4, "0")}.`);
  }

  console.log(`BufferMemory(messages=${buf.get().length}, ~${buf.tokenCount()} tokens)`);
  for (const m of buf.get()) console.log(`  [${m.role}] ${m.content.slice(0, 60)}`);

  assert.ok(buf.get().length <= 6, "max_messages eviction failed");
  assert.ok(buf.tokenCount() <= 200, "token eviction failed");
  assert.ok(buf.get()[0]?.role === "user", "buffer must start with a user turn (evict in pairs!)");
  console.log("\nAll eviction checks passed.");
}
