"""
M10 Lab: Hybrid Search (BM25 + Dense + RRF) and LLM Re-ranking
===============================================================
Run: python hybrid_rag.py
Requires: pip install openai chromadb rank-bm25
"""

import json

import chromadb
import numpy as np
from openai import OpenAI
from rank_bm25 import BM25Okapi

# ── The corpus (COMPLETE) — designed to break dense-only retrieval ──
DOCS = [
    "Metformin lowers blood sugar by reducing hepatic glucose production via AMPK activation.",
    "FDA approval number 123-456 was granted for metformin HCl 500mg tablets.",
    "Side effects of metformin include nausea, diarrhea, and abdominal discomfort.",
    "Drug interactions: iodinated contrast agents may cause lactic acidosis; hold metformin 48 hours before procedures.",
    "Metformin is contraindicated in patients with eGFR below 30 mL/min.",
    "FDA approval number 789-012 covers the extended-release formulation.",
    "Kidney function monitoring every 6 months is required for all metformin users.",
]
DOC_IDS = [f"doc-{i}" for i in range(len(DOCS))]


# ── Part 1: Reciprocal Rank Fusion (YOUR JOB) ────────────────
def rrf(rankings: list[list[str]], k: int = 60) -> dict[str, float]:
    """Merge ranked ID lists into one score dict.

    TODO: for each ranked_list, for each (rank, doc_id) starting at rank=1:
          scores[doc_id] += 1.0 / (k + rank)
    Return the scores dict. No score normalization — RRF uses RANKS only.
    """
    pass  # Remove this line when you add your code


# ── Part 2: HybridSearchIndex (search() is YOUR JOB) ─────────
class HybridSearchIndex:
    def __init__(self):
        client = chromadb.Client()
        try:
            client.delete_collection("hybrid_docs")
        except Exception:
            pass
        # ChromaDB's built-in embedder handles the dense side — no extra model
        self.collection = client.create_collection(
            "hybrid_docs", metadata={"hnsw:space": "cosine"}
        )
        self.docs: list[str] = []
        self.doc_ids: list[str] = []
        self.bm25: BM25Okapi | None = None

    def add_documents(self, docs: list[str], ids: list[str]) -> None:
        """(COMPLETE) Build BOTH indexes from the same doc list."""
        self.docs, self.doc_ids = docs, ids
        # BM25: tokenize by lowercasing + splitting on spaces
        self.bm25 = BM25Okapi([d.lower().split() for d in docs])
        # Dense: ChromaDB embeds on add
        self.collection.add(documents=docs, ids=ids)
        print(f"Indexed {len(docs)} documents (BM25 + dense)")

    def bm25_ranked(self, query: str, fetch_k: int = 20) -> list[str]:
        """(COMPLETE) Top fetch_k doc IDs by BM25 score."""
        scores = self.bm25.get_scores(query.lower().split())
        order = np.argsort(scores)[::-1][:fetch_k]
        return [self.doc_ids[i] for i in order]

    def dense_ranked(self, query: str, fetch_k: int = 20) -> list[str]:
        """(COMPLETE) Top fetch_k doc IDs by dense similarity."""
        results = self.collection.query(
            query_texts=[query], n_results=min(fetch_k, len(self.docs))
        )
        return results["ids"][0]  # already sorted by similarity

    def search(self, query: str, top_k: int = 5, fetch_k: int = 20) -> list[dict]:
        """Hybrid search: BM25 + dense + RRF merge.

        TODO:
        1. bm25_ids  = self.bm25_ranked(query, fetch_k)
           dense_ids = self.dense_ranked(query, fetch_k)
        2. rrf_scores = rrf([bm25_ids, dense_ids])
        3. sorted_ids = top_k IDs sorted by rrf_score descending
        4. Return [{"id": id, "text": <doc text>, "rrf_score": score}, ...]
           (build an id→text dict from self.doc_ids/self.docs)
        """
        pass  # Remove this line when you add your code


# ── Part 3: LLM Re-ranker (YOUR JOB) ─────────────────────────
client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

JUDGE_SYSTEM = (
    "You are a relevance judge. Score how relevant the document is to the "
    "query on a scale of 0.0 to 1.0. "
    'Respond with JSON only: {"score": 0.0}'
)


def llm_rerank(query: str, candidates: list[dict], top_k: int = 5) -> list[dict]:
    """Re-rank candidates using Mistral as a relevance judge.

    TODO: for each candidate:
    1. Call the model with JUDGE_SYSTEM and
       f"Query: {query}\\n\\nDocument: {c['text'][:500]}"
       (max_tokens=32, temperature=0)
    2. Parse the score DEFENSIVELY:
       raw = content.strip(); strip "```json" / "```" fences;
       score = float(json.loads(raw).get("score", 0.0))
       On ANY exception → score = 0.0 (never crash on a bad judgment)
    3. Attach as c["rerank_score"]
    Return candidates sorted by rerank_score descending, top_k only.
    """
    pass  # Remove this line when you add your code


# ── Test harness (COMPLETE) ──────────────────────────────────
if __name__ == "__main__":
    index = HybridSearchIndex()
    index.add_documents(DOCS, DOC_IDS)

    queries = [
        "FDA approval number 123-456",          # exact ID — dense usually fumbles this
        "what are the side effects",             # paraphrase — BM25 fumbles this
        "serious adverse reactions to the drug", # full paraphrase — needs dense + rerank
    ]

    for q in queries:
        print(f"\n{'=' * 60}\nQuery: {q!r}")
        print("  BM25-only top 3:  ", index.bm25_ranked(q, 3))
        print("  Dense-only top 3: ", index.dense_ranked(q, 3))
        hybrid = index.search(q, top_k=3)
        print("  Hybrid (RRF) top 3:")
        for r in hybrid:
            print(f"    [{r['rrf_score']:.4f}] {r['text'][:70]}")

    print(f"\n{'=' * 60}\nLLM re-rank of hybrid candidates for: 'serious adverse reactions to the drug'")
    candidates = index.search("serious adverse reactions to the drug", top_k=5)
    for r in llm_rerank("What are the serious adverse effects of metformin?", candidates, top_k=3):
        print(f"  [{r['rerank_score']:.2f}] {r['text'][:70]}")
