"""
M22 Lab - Part 1: Two-Layer Response Cache with TTL
====================================================
Layer 1: exact-match dict. Layer 2: semantic ChromaDB. Both expire.
Run: python agent_cache.py
Requires: pip install openai chromadb
"""

import hashlib
import time
from dataclasses import dataclass
from typing import Optional

import chromadb
from openai import OpenAI


@dataclass
class CacheEntry:
    """(COMPLETE)"""

    response: str
    created_at: float
    ttl_s: float

    def is_expired(self) -> bool:
        return time.time() > self.created_at + self.ttl_s


class AgentCache:
    """Layer 1: exact-match dict (hash of model+query).
    Layer 2: semantic vector cache via ChromaDB (cosine sim >= threshold).
    """

    def __init__(
        self,
        model: str = "mistral",
        similarity_threshold: float = 0.95,
        default_ttl_s: float = 3600.0,
    ):
        self.model = model
        self.threshold = similarity_threshold
        self.default_ttl = default_ttl_s
        self._exact: dict[str, CacheEntry] = {}  # Layer 1

        # Layer 2: in-process ChromaDB with its built-in embedder (COMPLETE)
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
        """(COMPLETE)"""
        return hashlib.sha256(f"{self.model}:{query}".encode()).hexdigest()[:16]

    def _purge_expired(self) -> None:
        """(COMPLETE) Layer-1 cleanup."""
        for k in [k for k, v in self._exact.items() if v.is_expired()]:
            del self._exact[k]

    def get(self, query: str) -> Optional[str]:
        """Check both layers; return the cached response or None.

        TODO:
        1. self._purge_expired()
        2. LAYER 1: key = self._hash_key(query); if key in self._exact and
           not expired → count "hits_exact", return entry.response
        3. LAYER 2 (wrap in try/except → fall through to None):
           results = self._collection.query(query_texts=[query], n_results=1,
               include=["documents", "distances", "metadatas"])
           If a document came back:
             similarity = 1 - results["distances"][0][0]   ← distance, not sim!
             expires_at = results["metadatas"][0][0].get("expires_at", 0)
             If similarity >= self.threshold and time.time() < expires_at:
               count "hits_semantic", return results["documents"][0][0]
        4. Return None
        """
        pass  # Remove this line when you add your code

    def set(self, query: str, response: str, ttl_s: Optional[float] = None) -> None:
        """Write BOTH layers.

        TODO:
        1. ttl = ttl_s or self.default_ttl; key = self._hash_key(query)
        2. LAYER 1: self._exact[key] = CacheEntry(response, time.time(), ttl)
        3. LAYER 2 (try/except pass — Layer 1 is sufficient fallback):
           self._collection.upsert(ids=[key], documents=[response],
               metadatas=[{"query": query[:200], "expires_at": time.time() + ttl}])
           NOTE: we EMBED THE QUERY by... storing the response as the document?
           No — query_texts in get() embeds the incoming query and matches
           against stored documents. To match query-to-query, store the QUERY
           as the document and keep the response in metadata? Both designs
           exist; THIS lab follows the course: the response is the document
           and similarity is measured query-to-response. It works because
           the response restates the entities from the query. (Stretch:
           refactor to query-as-document and compare hit rates.)
        """
        pass  # Remove this line when you add your code

    def infer(self, query: str, ttl_s: Optional[float] = None) -> str:
        """Full cache-aware inference: check cache, fall back to Ollama.

        TODO:
        1. cached = self.get(query); if not None: return it
        2. count "misses"
        3. response = self._client.chat.completions.create(model=self.model,
               messages=[{"role": "user", "content": query}], max_tokens=256)
           text = response.choices[0].message.content or ""
        4. self.set(query, text, ttl_s); return text
        """
        pass  # Remove this line when you add your code

    @property
    def stats(self) -> dict:
        """(COMPLETE)"""
        hits = self._stats["hits_exact"] + self._stats["hits_semantic"]
        total = hits + self._stats["misses"]
        return {**self._stats, "hit_rate": f"{hits / max(total, 1) * 100:.1f}%"}


# ── Smoke test (COMPLETE) ──
if __name__ == "__main__":
    cache = AgentCache()

    q1 = "What is the debtor name in UCC filing #12345? Answer in one sentence."
    q2 = "Who is the debtor listed on UCC-1 number 12345? One sentence."  # near-duplicate

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
    print("(If query 2 MISSED, the paraphrase fell under the 0.95 threshold —")
    print(" try 0.85 and observe the tradeoff. That judgment call is the lab.)")
