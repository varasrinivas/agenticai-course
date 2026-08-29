"""
M22 Lab — Response Cache (Solution)
====================================
Complete hash-based response cache with TTL expiry and LRU eviction.

Usage:
    python response_cache.py
"""

import hashlib
import time
import json


class ResponseCache:
    """
    In-memory response cache with TTL expiry and LRU eviction.

    Every query is normalized (lowercase, stripped, sorted params) and
    hashed with SHA-256. Responses are stored with a timestamp so we
    can expire stale entries. When the cache exceeds max_entries, the
    least recently used entry is evicted.
    """

    def __init__(self, ttl_seconds: int = 300, max_entries: int = 1000):
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        self.cache = {}
        self.stats = {"hits": 0, "misses": 0, "evictions": 0}
        # LRU order is tracked by a monotonic counter, NOT by the wall clock.
        # time.time() has ~15ms resolution on Windows, so three cache writes in
        # the same tick share an identical timestamp, min() ties, and the wrong
        # entry gets evicted. A counter cannot tie.
        self._access_seq = 0

    def _normalize_query(self, query: str, context: str = None) -> str:
        """Normalize query for consistent cache key generation."""
        # Lowercase and strip
        normalized = query.lower().strip()
        # Collapse multiple spaces into one
        normalized = " ".join(normalized.split())

        if context:
            try:
                # If context is JSON, sort keys for consistency
                parsed = json.loads(context)
                context_normalized = json.dumps(parsed, sort_keys=True)
            except (json.JSONDecodeError, TypeError):
                context_normalized = context.lower().strip()
            normalized = f"{normalized}|{context_normalized}"

        return normalized

    def _hash_key(self, query: str, context: str = None) -> str:
        """Create a SHA-256 hash from the normalized query + context."""
        normalized = self._normalize_query(query, context)
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def get(self, query: str, context: str = None) -> dict | None:
        """Retrieve a cached response if it exists and hasn't expired."""
        self._evict_expired()
        key = self._hash_key(query, context)

        if key in self.cache:
            entry = self.cache[key]
            # Check TTL
            if time.time() - entry["timestamp"] > self.ttl_seconds:
                del self.cache[key]
                self.stats["misses"] += 1
                return None
            # Update recency (for LRU). last_accessed stays for reporting;
            # lru_seq is what eviction actually orders by.
            entry["last_accessed"] = time.time()
            self._access_seq += 1
            entry["lru_seq"] = self._access_seq
            self.stats["hits"] += 1
            return entry["response"]

        self.stats["misses"] += 1
        return None

    def set(self, query: str, response: dict, context: str = None) -> None:
        """Store a response in the cache."""
        if len(self.cache) >= self.max_entries:
            self._evict_lru()
        key = self._hash_key(query, context)
        now = time.time()
        self._access_seq += 1
        self.cache[key] = {
            "response": response,
            "timestamp": now,
            "last_accessed": now,
            "lru_seq": self._access_seq,
        }

    def invalidate(self, query: str, context: str = None) -> bool:
        """Remove a specific entry from the cache."""
        key = self._hash_key(query, context)
        if key in self.cache:
            del self.cache[key]
            return True
        return False

    def clear(self) -> None:
        """Clear all entries and reset stats."""
        self.cache.clear()
        self.stats = {"hits": 0, "misses": 0, "evictions": 0}

    def get_stats(self) -> dict:
        """Return cache statistics."""
        total = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / total if total > 0 else 0.0
        return {
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "hit_rate": hit_rate,
            "entries": len(self.cache),
            "evictions": self.stats["evictions"],
        }

    def _evict_expired(self) -> None:
        """Remove all entries that have exceeded their TTL."""
        now = time.time()
        expired_keys = [
            k for k, v in self.cache.items()
            if now - v["timestamp"] > self.ttl_seconds
        ]
        for key in expired_keys:
            del self.cache[key]
            self.stats["evictions"] += 1

    def _evict_lru(self) -> None:
        """Remove the least recently used entry."""
        if not self.cache:
            return
        lru_key = min(self.cache, key=lambda k: self.cache[k]["lru_seq"])
        del self.cache[lru_key]
        self.stats["evictions"] += 1


# =============================================================================
# SELF-TEST
# =============================================================================

def self_test():
    """Test cache hits, misses, TTL expiry, and LRU eviction."""
    print("=" * 60)
    print("M22 Lab — Response Cache Self-Test")
    print("=" * 60)

    # --- Test 1: Basic set and get ---
    print("\n--- Test 1: Basic set and get ---")
    cache = ResponseCache(ttl_seconds=5, max_entries=3)

    cache.set("Find filings for Acme Corp", {"answer": "Found 3 filings", "model": "sonnet"})
    result = cache.get("Find filings for Acme Corp")
    assert result is not None, "FAIL: Should have found cached response"
    assert result["answer"] == "Found 3 filings"
    print(f"  PASS: Cached and retrieved response: {result['answer']}")

    # --- Test 2: Normalization ---
    print("\n--- Test 2: Query normalization ---")
    result2 = cache.get("  FIND  FILINGS  FOR  ACME  CORP  ")
    assert result2 is not None, "FAIL: Normalized query should hit cache"
    print(f"  PASS: Normalized query matched: {result2['answer']}")

    # --- Test 3: Cache miss ---
    print("\n--- Test 3: Cache miss ---")
    result3 = cache.get("Totally different query")
    assert result3 is None, "FAIL: Should be a cache miss"
    print(f"  PASS: Cache miss returned None")

    # --- Test 4: TTL expiry ---
    print("\n--- Test 4: TTL expiry (short TTL) ---")
    short_cache = ResponseCache(ttl_seconds=1, max_entries=10)
    short_cache.set("expiring query", {"answer": "temporary"})
    result4 = short_cache.get("expiring query")
    assert result4 is not None, "FAIL: Should be cached immediately"
    print(f"  Cached response found (before expiry)")

    print(f"  Waiting 1.5 seconds for TTL expiry...")
    time.sleep(1.5)

    result4b = short_cache.get("expiring query")
    assert result4b is None, "FAIL: Should have expired"
    print(f"  PASS: Response expired after TTL")

    # --- Test 5: LRU eviction ---
    print("\n--- Test 5: LRU eviction (max_entries=3) ---")
    lru_cache = ResponseCache(ttl_seconds=300, max_entries=3)
    lru_cache.set("query A", {"answer": "A"})
    lru_cache.set("query B", {"answer": "B"})
    lru_cache.set("query C", {"answer": "C"})

    # Access A to make it recently used
    lru_cache.get("query A")

    # Add D — should evict B (least recently used)
    lru_cache.set("query D", {"answer": "D"})

    assert lru_cache.get("query A") is not None, "FAIL: A should still be cached"
    assert lru_cache.get("query B") is None, "FAIL: B should have been evicted"
    assert lru_cache.get("query D") is not None, "FAIL: D should be cached"
    print(f"  PASS: LRU eviction removed oldest entry (B)")

    # --- Test 6: Invalidation ---
    print("\n--- Test 6: Invalidation ---")
    cache.set("to remove", {"answer": "bye"})
    removed = cache.invalidate("to remove")
    assert removed is True, "FAIL: Should return True"
    assert cache.get("to remove") is None, "FAIL: Should be gone"
    print(f"  PASS: Entry invalidated successfully")

    # --- Test 7: Stats ---
    print("\n--- Test 7: Cache stats ---")
    stats = cache.get_stats()
    print(f"  Hits: {stats['hits']}, Misses: {stats['misses']}, "
          f"Hit Rate: {stats['hit_rate']:.1%}, Evictions: {stats['evictions']}")
    assert stats["hits"] > 0, "FAIL: Should have recorded hits"
    assert stats["misses"] > 0, "FAIL: Should have recorded misses"
    print(f"  PASS: Stats tracking works")

    print("\n" + "=" * 60)
    print("All cache tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    self_test()
