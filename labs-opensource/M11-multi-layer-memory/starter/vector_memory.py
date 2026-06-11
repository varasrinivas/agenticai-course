"""
M11 Lab - Step 2: VectorMemory (Layer 2 — across sessions)
===========================================================
Persistent semantic store on ChromaDB. Survives process restarts.
Run: python vector_memory.py
"""

from __future__ import annotations

import uuid
from typing import Optional

import chromadb
from chromadb.config import Settings


class VectorMemory:
    """Semantic memory backed by ChromaDB (local SQLite persistence).

    Embeddings come from ChromaDB's built-in model — fully local, no API key.
    (The course version uses sentence-transformers explicitly; same idea.)
    """

    def __init__(
        self,
        persist_directory: str = "./chroma_memory",
        collection_name: str = "agent_memory",
        dedup_threshold: float = 0.95,
    ) -> None:
        # PersistentClient — data survives process restarts (COMPLETE)
        self._client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        self.dedup_threshold = dedup_threshold

    def save(self, text: str, metadata: Optional[dict] = None) -> str:
        """Store text; skip if a near-duplicate exists. Returns the memory ID.

        TODO:
        1. DEDUP: if self._collection.count() > 0:
           existing = self._collection.query(query_texts=[text], n_results=1,
                                             include=["distances"])
           ChromaDB cosine DISTANCE = 1 - similarity, so:
           cosine_sim = 1.0 - existing["distances"][0][0]
           If cosine_sim >= self.dedup_threshold: return existing["ids"][0][0]
        2. memory_id = str(uuid.uuid4())
        3. safe_meta = only the (str, int, float, bool) values of metadata —
           ChromaDB rejects nested objects
        4. self._collection.add(ids=[memory_id], documents=[text],
                                metadatas=[safe_meta] if safe_meta else None)
        5. Return memory_id
        """
        pass  # Remove this line when you add your code

    def recall(self, query: str, k: int = 5) -> list[dict]:
        """Return up to k memories most similar to query.

        TODO:
        1. count = self._collection.count(); if 0: return []
        2. results = self._collection.query(query_texts=[query],
               n_results=min(k, count), include=["documents", "metadatas", "distances"])
        3. For each hit, build {"id", "text" (the document), "score" (1 - distance,
           rounded to 4 dp), "metadata"}
        4. Return sorted by score descending
        """
        pass  # Remove this line when you add your code

    def forget(self, memory_id: str) -> bool:
        """(COMPLETE) Delete memory by ID."""
        try:
            self._collection.delete(ids=[memory_id])
            return True
        except Exception:
            return False

    def count(self) -> int:
        return self._collection.count()


# ── Smoke test (COMPLETE) ──
if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        mem = VectorMemory(persist_directory=tmp)

        id1 = mem.save("Order TRK-001 was shipped via FedEx on Monday", {"order_id": "TRK-001"})
        id2 = mem.save("Customer prefers email notifications over SMS", {"type": "preference"})
        id3 = mem.save("The order was delayed due to a weather event in Memphis", {"order_id": "TRK-001"})
        # Dedup check: near-identical text should return the EXISTING id
        id4 = mem.save("Order TRK-001 was shipped via FedEx on Monday", {"order_id": "TRK-001"})

        print(f"Stored {mem.count()} memories (expected 3 — the 4th was a duplicate)")
        assert id4 == id1, "dedup failed: identical text created a new memory"

        results = mem.recall("What happened with the delivery?", k=3)
        for r in results:
            print(f"  [{r['score']:.3f}] {r['text'][:70]}")
        print("\nDedup + recall checks passed.")
