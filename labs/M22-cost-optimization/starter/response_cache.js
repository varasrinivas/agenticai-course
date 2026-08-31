/**
 * M22 Lab — Response Cache (Starter)
 * ===================================
 * Build a hash-based response cache with TTL expiry and LRU eviction.
 * The cache normalizes queries so that "Find  filings" and "find filings"
 * produce the same cache key, improving hit rates.
 *
 * KEY CONCEPT: Caching is the single biggest cost saver. If a user asks
 * the same question twice within 5 minutes, there is zero reason to burn
 * tokens on a second API call. A good cache pays for itself on Day 1.
 *
 * Usage:
 *     node response_cache.js
 */

import crypto from "crypto";
import assert from "node:assert/strict";

class ResponseCache {
  /**
   * In-memory response cache with TTL expiry and LRU eviction.
   *
   * @param {number} ttlSeconds - Time-to-live for each entry (default 300)
   * @param {number} maxEntries - Maximum cached entries before LRU eviction (default 1000)
   */
  constructor(ttlSeconds = 300, maxEntries = 1000) {
    this.ttlSeconds = ttlSeconds;
    this.maxEntries = maxEntries;
    this.cache = new Map();
    this.stats = { hits: 0, misses: 0, evictions: 0 };
  }

  /**
   * Normalize query for consistent cache key generation.
   * - Lowercase, strip whitespace, collapse multiple spaces
   * - If context is JSON, sort keys for consistency
   *
   * @param {string} query
   * @param {string|null} context
   * @returns {string}
   */
  _normalizeQuery(query, context = null) {
    // TODO: Implement normalization
    // 1. Lowercase the query
    // 2. Trim whitespace
    // 3. Collapse multiple spaces into single spaces
    // 4. If context is provided, try JSON.parse and JSON.stringify with sorted keys
    //    If not valid JSON, just lowercase and trim
    // 5. Return combined string: `${normalized}` or `${normalized}|${contextNormalized}`
  }

  /**
   * Create a SHA-256 hash from the normalized query + context.
   *
   * @param {string} query
   * @param {string|null} context
   * @returns {string}
   */
  _hashKey(query, context = null) {
    // TODO: Implement hash key generation
    // 1. Get normalized text from _normalizeQuery
    // 2. Create SHA-256 hash using crypto.createHash
    // 3. Return hex digest
  }

  /**
   * Retrieve a cached response if it exists and hasn't expired.
   *
   * @param {string} query
   * @param {string|null} context
   * @returns {object|null}
   */
  get(query, context = null) {
    // TODO: Implement cache lookup
    // 1. Call _evictExpired()
    // 2. Generate hash key
    // 3. If key exists:
    //    a. Check TTL expiry (Date.now() - entry.timestamp > ttlSeconds * 1000)
    //    b. If expired: delete, increment misses, return null
    //    c. If valid: update lastAccessed, increment hits, return response
    // 4. If not found: increment misses, return null
  }

  /**
   * Store a response in the cache.
   *
   * @param {string} query
   * @param {object} response
   * @param {string|null} context
   */
  set(query, response, context = null) {
    // TODO: Implement cache storage
    // 1. If cache.size >= maxEntries, call _evictLru()
    // 2. Generate hash key
    // 3. Store entry with response, timestamp (Date.now()), lastAccessed
  }

  /**
   * Remove a specific entry from the cache.
   *
   * @param {string} query
   * @param {string|null} context
   * @returns {boolean}
   */
  invalidate(query, context = null) {
    // TODO: Generate hash key; if exists, delete and return true; else false
  }

  /** Clear all entries and reset stats. */
  clear() {
    // TODO: Clear cache Map and reset stats
  }

  /**
   * Return cache statistics.
   * @returns {{hits: number, misses: number, hitRate: number, entries: number, evictions: number}}
   */
  getStats() {
    // TODO: Calculate hitRate = hits / (hits + misses) or 0
  }

  /** Remove all entries that have exceeded their TTL. */
  _evictExpired() {
    // TODO: Iterate cache entries, delete any where Date.now() - timestamp > ttlSeconds * 1000
    // Increment this.stats.evictions for each
  }

  /** Remove the least recently used entry. */
  _evictLru() {
    // TODO: Find entry with smallest lastAccessed, delete it
    // Increment this.stats.evictions
  }
}

// =============================================================================
// SELF-TEST
// =============================================================================

async function selfTest() {
  console.log("=".repeat(60));
  console.log("M22 Lab — Response Cache Self-Test");
  console.log("=".repeat(60));

  // --- Test 1: Basic set and get ---
  console.log("\n--- Test 1: Basic set and get ---");
  const cache = new ResponseCache(5, 3);
  cache.set("Find filings for Acme Corp", {
    answer: "Found 3 filings",
    model: "sonnet",
  });
  let result = cache.get("Find filings for Acme Corp");
  assert.ok(result !== null, "FAIL: Should have found cached response");
  console.log(`  PASS: Cached and retrieved response: ${result.answer}`);

  // --- Test 2: Normalization ---
  console.log("\n--- Test 2: Query normalization ---");
  let result2 = cache.get("  FIND  FILINGS  FOR  ACME  CORP  ");
  assert.ok(result2 !== null, "FAIL: Normalized query should hit cache");
  console.log(`  PASS: Normalized query matched: ${result2.answer}`);

  // --- Test 3: Cache miss ---
  console.log("\n--- Test 3: Cache miss ---");
  let result3 = cache.get("Totally different query");
  assert.ok(result3 === null, "FAIL: Should be a cache miss");
  console.log("  PASS: Cache miss returned null");

  // --- Test 4: TTL expiry ---
  console.log("\n--- Test 4: TTL expiry (short TTL) ---");
  const shortCache = new ResponseCache(1, 10);
  shortCache.set("expiring query", { answer: "temporary" });
  let result4 = shortCache.get("expiring query");
  assert.ok(result4 !== null, "FAIL: Should be cached immediately");
  console.log("  Cached response found (before expiry)");
  console.log("  Waiting 1.5 seconds for TTL expiry...");

  await new Promise((r) => setTimeout(r, 1500));

  let result4b = shortCache.get("expiring query");
  assert.ok(result4b === null, "FAIL: Should have expired");
  console.log("  PASS: Response expired after TTL");

  // --- Test 5: LRU eviction ---
  console.log("\n--- Test 5: LRU eviction (max_entries=3) ---");
  const lruCache = new ResponseCache(300, 3);
  lruCache.set("query A", { answer: "A" });
  lruCache.set("query B", { answer: "B" });
  lruCache.set("query C", { answer: "C" });

  lruCache.get("query A"); // Make A recently used

  lruCache.set("query D", { answer: "D" }); // Should evict B

  assert.ok(lruCache.get("query A") !== null, "FAIL: A should still be cached");
  assert.ok(lruCache.get("query B") === null, "FAIL: B should have been evicted");
  assert.ok(lruCache.get("query D") !== null, "FAIL: D should be cached");
  console.log("  PASS: LRU eviction removed oldest entry (B)");

  // --- Test 6: Invalidation ---
  console.log("\n--- Test 6: Invalidation ---");
  cache.set("to remove", { answer: "bye" });
  let removed = cache.invalidate("to remove");
  assert.ok(removed === true, "FAIL: Should return true");
  assert.ok(cache.get("to remove") === null, "FAIL: Should be gone");
  console.log("  PASS: Entry invalidated successfully");

  // --- Test 7: Stats ---
  console.log("\n--- Test 7: Cache stats ---");
  const stats = cache.getStats();
  console.log(
    `  Hits: ${stats.hits}, Misses: ${stats.misses}, ` +
      `Hit Rate: ${(stats.hitRate * 100).toFixed(1)}%, Evictions: ${stats.evictions}`
  );
  assert.ok(stats.hits > 0, "FAIL: Should have recorded hits");
  assert.ok(stats.misses > 0, "FAIL: Should have recorded misses");
  console.log("  PASS: Stats tracking works");

  console.log("\n" + "=".repeat(60));
  console.log("All cache tests passed!");
  console.log("=".repeat(60));
}

selfTest();

export { ResponseCache };
