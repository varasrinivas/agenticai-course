"""
M11 Lab - Step 2: VectorMemory — SOLUTION
==========================================
Run: python vector_memory.py
"""

from __future__ import annotations

import uuid
from typing import Optional

import chromadb
from chromadb.config import Settings


class VectorMemory:
    """Semantic memory backed by ChromaDB (local SQLite persistence)."""

    def __init__(
        self,
        persist_directory: str = "./chroma_memory",
        collection_name: str = "agent_memory",
        dedup_threshold: float = 0.95,
    ) -> None:
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
        """Store text; skip if a near-duplicate exists. Returns the memory ID."""
        # Deduplication check — ChromaDB cosine DISTANCE = 1 - similarity
        if self._collection.count() > 0:
            existing = self._collection.query(
                query_texts=[text], n_results=1, include=["distances"]
            )
            if existing["distances"] and existing["distances"][0]:
                cosine_sim = 1.0 - existing["distances"][0][0]
                if cosine_sim >= self.dedup_threshold:
                    return existing["ids"][0][0]  # near-duplicate: reuse

        memory_id = str(uuid.uuid4())
        safe_meta = {
            k: v for k, v in (metadata or {}).items()
            if isinstance(v, (str, int, float, bool))
        }
        self._collection.add(
            ids=[memory_id],
            documents=[text],
            metadatas=[safe_meta] if safe_meta else None,
        )
        return memory_id

    def recall(self, query: str, k: int = 5) -> list[dict]:
        """Return up to k memories most similar to query."""
        count = self._collection.count()
        if count == 0:
            return []

        results = self._collection.query(
            query_texts=[query],
            n_results=min(k, count),
            include=["documents", "metadatas", "distances"],
        )

        memories = []
        for i, mem_id in enumerate(results["ids"][0]):
            distance = results["distances"][0][i]
            memories.append({
                "id": mem_id,
                "text": results["documents"][0][i],
                "score": round(1.0 - distance, 4),
                "metadata": results["metadatas"][0][i] or {},
            })

        return sorted(memories, key=lambda m: m["score"], reverse=True)

    def forget(self, memory_id: str) -> bool:
        try:
            self._collection.delete(ids=[memory_id])
            return True
        except Exception:
            return False

    def count(self) -> int:
        return self._collection.count()


if __name__ == "__main__":
    import tempfile

    # ignore_cleanup_errors because Chroma keeps chroma.sqlite3 open, and
    # Windows refuses to delete an open file -- without it this demo prints
    # all its passing checks and then dies with a NotADirectoryError from
    # shutil.rmtree, which looks like the lab failing when it did not.
    # (Python 3.10+, which this course already requires.)
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        mem = VectorMemory(persist_directory=tmp)

        id1 = mem.save("Order TRK-001 was shipped via FedEx on Monday", {"order_id": "TRK-001"})
        id2 = mem.save("Customer prefers email notifications over SMS", {"type": "preference"})
        id3 = mem.save("The order was delayed due to a weather event in Memphis", {"order_id": "TRK-001"})
        id4 = mem.save("Order TRK-001 was shipped via FedEx on Monday", {"order_id": "TRK-001"})

        print(f"Stored {mem.count()} memories (expected 3 — the 4th was a duplicate)")
        assert id4 == id1, "dedup failed: identical text created a new memory"

        results = mem.recall("What happened with the delivery?", k=3)
        for r in results:
            print(f"  [{r['score']:.3f}] {r['text'][:70]}")
        print("\nDedup + recall checks passed.")
