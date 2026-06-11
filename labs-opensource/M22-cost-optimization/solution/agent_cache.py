"""
M22 Lab - Part 1: Two-Layer Response Cache with TTL — SOLUTION
===============================================================
Run: python agent_cache.py
"""

import hashlib
import time
from dataclasses import dataclass
from typing import Optional

import chromadb
from openai import OpenAI


@dataclass
class CacheEntry:
    response: str
    created_at: float
    ttl_s: float

    def is_expired(self) -> bool:
        return time.time() > self.created_at + self.ttl_s


class AgentCache:
    """Layer 1: exact-match dict. Layer 2: semantic ChromaDB. Both expire."""

    def __init__(
        self,
        model: str = "mistral",
        similarity_threshold: float = 0.95,
        default_ttl_s: float = 3600.0,
    ):
        self.model = model
        self.threshold = similarity_threshold
        self.default_ttl = default_ttl_s
        self._exact: dict[str, CacheEntry] = {}

        self._chroma = chromadb.Client()
        try:
            self._chroma.delete_collection("agent_cache")
        except Exception:
            pass
        self._collection = self._chroma.create_collection(
            name="agent_cache", metadata={"hnsw:space": "cosine"}
        )
        self._client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
        self._stats = {"hits_exact": 0, "hits_semantic": 0, "misses": 0}

    def _hash_key(self, query: str) -> str:
        return hashlib.sha256(f"{self.model}:{query}".encode()).hexdigest()[:16]

    def _purge_expired(self) -> None:
        for k in [k for k, v in self._exact.items() if v.is_expired()]:
            del self._exact[k]

    def get(self, query: str) -> Optional[str]:
        """Check both layers; return the cached response or None."""
        self._purge_expired()

        # Layer 1: exact match
        key = self._hash_key(query)
        if key in self._exact and not self._exact[key].is_expired():
            self._stats["hits_exact"] += 1
            return self._exact[key].response

        # Layer 2: semantic similarity
        try:
            results = self._collection.query(
                query_texts=[query],
                n_results=1,
                include=["documents", "distances", "metadatas"],
            )
            if results["documents"] and results["documents"][0]:
                similarity = 1 - results["distances"][0][0]  # distance -> similarity
                expires_at = results["metadatas"][0][0].get("expires_at", 0)
                if similarity >= self.threshold and time.time() < expires_at:
                    self._stats["hits_semantic"] += 1
                    return results["documents"][0][0]
        except Exception:
            pass

        return None

    def set(self, query: str, response: str, ttl_s: Optional[float] = None) -> None:
        """Write BOTH layers."""
        ttl = ttl_s or self.default_ttl
        key = self._hash_key(query)

        # Layer 1
        self._exact[key] = CacheEntry(response=response, created_at=time.time(), ttl_s=ttl)

        # Layer 2 — failures swallowed; Layer 1 is sufficient fallback
        try:
            self._collection.upsert(
                ids=[key],
                documents=[response],
                metadatas=[{"query": query[:200], "expires_at": time.time() + ttl}],
            )
        except Exception:
            pass

    def infer(self, query: str, ttl_s: Optional[float] = None) -> str:
        """Full cache-aware inference: check cache, fall back to Ollama."""
        cached = self.get(query)
        if cached is not None:
            return cached

        self._stats["misses"] += 1
        response = self._client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": query}],
            max_tokens=256,
        )
        text = response.choices[0].message.content or ""
        self.set(query, text, ttl_s)
        return text

    @property
    def stats(self) -> dict:
        hits = self._stats["hits_exact"] + self._stats["hits_semantic"]
        total = hits + self._stats["misses"]
        return {**self._stats, "hit_rate": f"{hits / max(total, 1) * 100:.1f}%"}


if __name__ == "__main__":
    cache = AgentCache()

    q1 = "What is the debtor name in UCC filing #12345? Answer in one sentence."
    q2 = "Who is the debtor listed on UCC-1 number 12345? One sentence."

    print("Query 1 (expect MISS — runs Ollama)...")
    t0 = time.perf_counter()
    r1 = cache.infer(q1)
    print(f"  {time.perf_counter() - t0:.1f}s  {r1[:80]}")

    print("Query 1 again (expect EXACT hit — instant)...")
    t0 = time.perf_counter()
    r2 = cache.infer(q1)
    print(f"  {time.perf_counter() - t0:.3f}s  {r2[:80]}")
    assert r2 == r1

    print("Query 2, a paraphrase (semantic hit if similarity >= 0.95)...")
    t0 = time.perf_counter()
    r3 = cache.infer(q2)
    print(f"  {time.perf_counter() - t0:.1f}s  {r3[:80]}")

    print(f"\nStats: {cache.stats}")
