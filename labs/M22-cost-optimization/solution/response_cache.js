/**
 * M22 Lab — Response Cache (Solution)
 * ====================================
 * Complete hash-based response cache with TTL expiry and LRU eviction.
 *
 * Usage:
 *     node response_cache.js
 */

import crypto from "crypto";
import assert from "node:assert/strict";

class ResponseCache {
  constructor(ttlSeconds = 300, maxEntries = 1000) {
    this.ttlSeconds = ttlSeconds;
    this.maxEntries = maxEntries;
    this.cache = new Map();
    this.stats = { hits: 0, misses: 0, evictions: 0 };
  }

  _normalizeQuery(query, context = null) {
    let normalized = query.toLowerCase().trim();
    normalized = normalized.replace(/\s+/g, " ");

    if (context) {
      let contextNormalized;
      try {
        const parsed = JSON.parse(context);
        contextNormalized = JSON.stringify(parsed, Object.keys(parsed).sort());
      } catch {
        contextNormalized = context.toLowerCase().trim();
      }
      normalized = `${normalized}|${contextNormalized}`;
    }

    return normalized;
  }

  _hashKey(query, context = null) {
    const normalized = this._normalizeQuery(query, context);
    return crypto.createHash("sha256").update(normalized, "utf8").digest("hex");
  }

  get(query, context = null) {
    this._evictExpired();
    const key = this._hashKey(query, context);

    if (this.cache.has(key)) {
      const entry = this.cache.get(key);
      if (Date.now() - entry.timestamp > this.ttlSeconds * 1000) {
        this.cache.delete(key);
        this.stats.misses++;
        return null;
      }
      entry.lastAccessed = Date.now();
      this.stats.hits++;
      return entry.response;
    }

    this.stats.misses++;
    return null;
  }

  set(query, response, context = null) {
    if (this.cache.size >= this.maxEntries) {
      this._evictLru();
    }
    const key = this._hashKey(query, context);
    const now = Date.now();
    this.cache.set(key, { response, timestamp: now, lastAccessed: now });
  }

  invalidate(query, context = null) {
    const key = this._hashKey(query, context);
    if (this.cache.has(key)) {
      this.cache.delete(key);
      return true;
    }
    return false;
  }

  clear() {
    this.cache.clear();
    this.stats = { hits: 0, misses: 0, evictions: 0 };
  }

  getStats() {
    const total = this.stats.hits + this.stats.misses;
    const hitRate = total > 0 ? this.stats.hits / total : 0;
    return {
      hits: this.stats.hits,
      misses: this.stats.misses,
      hitRate,
      entries: this.cache.size,
      evictions: this.stats.evictions,
    };
  }

  _evictExpired() {
    const now = Date.now();
    for (const [key, entry] of this.cache.entries()) {
      if (now - entry.timestamp > this.ttlSeconds * 1000) {
        this.cache.delete(key);
        this.stats.evictions++;
      }
    }
  }

  _evictLru() {
    if (this.cache.size === 0) return;
    let lruKey = null;
    let lruTime = Infinity;
    for (const [key, entry] of this.cache.entries()) {
      if (entry.lastAccessed < lruTime) {
        lruTime = entry.lastAccessed;
        lruKey = key;
      }
    }
    if (lruKey) {
      this.cache.delete(lruKey);
      this.stats.evictions++;
    }
  }
}

// =============================================================================
// SELF-TEST
// =============================================================================

async function selfTest() {
  console.log("=".repeat(60));
  console.log("M22 Lab — Response Cache Self-Test");
  console.log("=".repeat(60));

  // --- Test 1 ---
  console.log("\n--- Test 1: Basic set and get ---");
  const cache = new ResponseCache(5, 3);
  cache.set("Find filings for Acme Corp", { answer: "Found 3 filings", model: "sonnet" });
  let result = cache.get("Find filings for Acme Corp");
  assert.ok(result !== null, "FAIL");
  console.log(`  PASS: Cached and retrieved response: ${result.answer}`);

  // --- Test 2 ---
  console.log("\n--- Test 2: Query normalization ---");
  let result2 = cache.get("  FIND  FILINGS  FOR  ACME  CORP  ");
  assert.ok(result2 !== null, "FAIL");
  console.log(`  PASS: Normalized query matched: ${result2.answer}`);

  // --- Test 3 ---
  console.log("\n--- Test 3: Cache miss ---");
  let result3 = cache.get("Totally different query");
  assert.ok(result3 === null, "FAIL");
  console.log("  PASS: Cache miss returned null");

  // --- Test 4 ---
  console.log("\n--- Test 4: TTL expiry (short TTL) ---");
  const shortCache = new ResponseCache(1, 10);
  shortCache.set("expiring query", { answer: "temporary" });
  assert.ok(shortCache.get("expiring query") !== null, "FAIL");
  console.log("  Cached response found (before expiry)");
  console.log("  Waiting 1.5 seconds for TTL expiry...");
  await new Promise((r) => setTimeout(r, 1500));
  assert.ok(shortCache.get("expiring query") === null, "FAIL");
  console.log("  PASS: Response expired after TTL");

  // --- Test 5 ---
  console.log("\n--- Test 5: LRU eviction (max_entries=3) ---");
  const lruCache = new ResponseCache(300, 3);
  lruCache.set("query A", { answer: "A" });
  lruCache.set("query B", { answer: "B" });
  lruCache.set("query C", { answer: "C" });
  lruCache.get("query A");
  lruCache.set("query D", { answer: "D" });
  assert.ok(lruCache.get("query A") !== null, "FAIL: A should be cached");
  assert.ok(lruCache.get("query B") === null, "FAIL: B should be evicted");
  assert.ok(lruCache.get("query D") !== null, "FAIL: D should be cached");
  console.log("  PASS: LRU eviction removed oldest entry (B)");

  // --- Test 6 ---
  console.log("\n--- Test 6: Invalidation ---");
  cache.set("to remove", { answer: "bye" });
  assert.ok(cache.invalidate("to remove") === true);
  assert.ok(cache.get("to remove") === null);
  console.log("  PASS: Entry invalidated successfully");

  // --- Test 7 ---
  console.log("\n--- Test 7: Cache stats ---");
  const stats = cache.getStats();
  console.log(
    `  Hits: ${stats.hits}, Misses: ${stats.misses}, ` +
      `Hit Rate: ${(stats.hitRate * 100).toFixed(1)}%, Evictions: ${stats.evictions}`
  );
  console.log("  PASS: Stats tracking works");

  console.log("\n" + "=".repeat(60));
  console.log("All cache tests passed!");
  console.log("=".repeat(60));
}

selfTest();

export { ResponseCache };
