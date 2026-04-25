"""
M22 Lab — Response Cache (Starter)
===================================
Build a hash-based response cache with TTL expiry and LRU eviction.
The cache normalizes queries so that "Find  filings" and "find filings"
produce the same cache key, improving hit rates.

KEY CONCEPT: Caching is the single biggest cost saver. If a user asks
the same question twice within 5 minutes, there is zero reason to burn
tokens on a second API call. A good cache pays for itself on Day 1.

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
        """
        Initialize the cache.

        Args:
            ttl_seconds: Time-to-live for each entry in seconds (default 5 min)
            max_entries: Maximum number of cached responses before LRU eviction
        """
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        self.cache = {}  # key -> {"response": ..., "timestamp": ..., "last_accessed": ...}
        self.stats = {"hits": 0, "misses": 0, "evictions": 0}

    def _normalize_query(self, query: str, context: str = None) -> str:
        """
        Normalize query for consistent cache key generation.

        - Lowercase the query
        - Strip leading/trailing whitespace
        - Collapse multiple spaces into one
        - If context is provided, sort its key-value pairs for consistency

        Args:
            query: The user query string
            context: Optional context string (JSON or plain text)

        Returns:
            Normalized string combining query and context
        """
        # TODO: Implement normalization
        # 1. Lowercase the query
        # 2. Strip whitespace
        # 3. Collapse multiple spaces into single spaces
        # 4. If context is provided, try to parse as JSON and sort keys
        #    If not JSON, just lowercase and strip
        # 5. Return combined normalized string
        pass

    def _hash_key(self, query: str, context: str = None) -> str:
        """
        Create a SHA-256 hash from the normalized query + context.

        Args:
            query: The user query
            context: Optional context

        Returns:
            Hex digest of SHA-256 hash
        """
        # TODO: Implement hash key generation
        # 1. Call _normalize_query to get normalized text
        # 2. Encode as UTF-8
        # 3. Return SHA-256 hex digest
        pass

    def get(self, query: str, context: str = None) -> dict | None:
        """
        Retrieve a cached response if it exists and hasn't expired.

        Args:
            query: The user query
            context: Optional context

        Returns:
            Cached response dict or None if miss/expired
        """
        # TODO: Implement cache lookup
        # 1. Run _evict_expired() to clean stale entries first
        # 2. Generate hash key
        # 3. If key exists in cache:
        #    a. Check if entry has expired (current time - timestamp > ttl)
        #    b. If expired: delete entry, increment misses, return None
        #    c. If valid: update last_accessed time, increment hits, return response
        # 4. If key not in cache: increment misses, return None
        pass

    def set(self, query: str, response: dict, context: str = None) -> None:
        """
        Store a response in the cache.

        Args:
            query: The user query
            response: The response dict to cache
            context: Optional context
        """
        # TODO: Implement cache storage
        # 1. If cache is at max_entries, call _evict_lru()
        # 2. Generate hash key
        # 3. Store entry with response, current timestamp, and last_accessed time
        pass

    def invalidate(self, query: str, context: str = None) -> bool:
        """
        Remove a specific entry from the cache.

        Args:
            query: The query to invalidate
            context: Optional context

        Returns:
            True if entry was found and removed, False otherwise
        """
        # TODO: Implement cache invalidation
        # 1. Generate hash key
        # 2. If key exists, delete it and return True
        # 3. Otherwise return False
        pass

    def clear(self) -> None:
        """Clear all entries and reset stats."""
        # TODO: Clear cache dict and reset stats
        pass

    def get_stats(self) -> dict:
        """
        Return cache statistics.

        Returns:
            Dict with hits, misses, hit_rate, entries, evictions
        """
        # TODO: Calculate and return stats
        # hit_rate = hits / (hits + misses) if any lookups happened, else 0.0
        pass

    def _evict_expired(self) -> None:
        """Remove all entries that have exceeded their TTL."""
        # TODO: Iterate through cache and remove expired entries
        # An entry is expired if: current_time - entry["timestamp"] > ttl_seconds
        # Increment self.stats["evictions"] for each evicted entry
        pass

    def _evict_lru(self) -> None:
        """Remove the least recently used entry."""
        # TODO: Find the entry with the oldest last_accessed time and remove it
        # Increment self.stats["evictions"]
        pass


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

    # --- Test 2: Normalization (case-insensitive, whitespace-tolerant) ---
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
