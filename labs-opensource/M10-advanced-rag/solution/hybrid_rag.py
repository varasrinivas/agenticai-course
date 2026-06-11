"""
M10 Lab: Hybrid Search (BM25 + Dense + RRF) and LLM Re-ranking — SOLUTION
==========================================================================
Run: python hybrid_rag.py
"""

import json

import chromadb
import numpy as np
from openai import OpenAI
from rank_bm25 import BM25Okapi

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


def rrf(rankings: list[list[str]], k: int = 60) -> dict[str, float]:
    """Reciprocal Rank Fusion: merge ranked ID lists using ranks only."""
    scores: dict[str, float] = {}
    for ranked_list in rankings:
        for rank, doc_id in enumerate(ranked_list, start=1):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)
    return scores


class HybridSearchIndex:
    def __init__(self):
        client = chromadb.Client()
        try:
            client.delete_collection("hybrid_docs")
        except Exception:
            pass
        self.collection = client.create_collection(
            "hybrid_docs", metadata={"hnsw:space": "cosine"}
        )
        self.docs: list[str] = []
        self.doc_ids: list[str] = []
        self.bm25: BM25Okapi | None = None

    def add_documents(self, docs: list[str], ids: list[str]) -> None:
        self.docs, self.doc_ids = docs, ids
        self.bm25 = BM25Okapi([d.lower().split() for d in docs])
        self.collection.add(documents=docs, ids=ids)
        print(f"Indexed {len(docs)} documents (BM25 + dense)")

    def bm25_ranked(self, query: str, fetch_k: int = 20) -> list[str]:
        scores = self.bm25.get_scores(query.lower().split())
        order = np.argsort(scores)[::-1][:fetch_k]
        return [self.doc_ids[i] for i in order]

    def dense_ranked(self, query: str, fetch_k: int = 20) -> list[str]:
        results = self.collection.query(
            query_texts=[query], n_results=min(fetch_k, len(self.docs))
        )
        return results["ids"][0]

    def search(self, query: str, top_k: int = 5, fetch_k: int = 20) -> list[dict]:
        """Hybrid search: BM25 + dense + RRF merge."""
        bm25_ids = self.bm25_ranked(query, fetch_k)
        dense_ids = self.dense_ranked(query, fetch_k)

        rrf_scores = rrf([bm25_ids, dense_ids])
        sorted_ids = sorted(rrf_scores, key=rrf_scores.get, reverse=True)[:top_k]

        id_to_doc = dict(zip(self.doc_ids, self.docs))
        return [
            {"id": doc_id, "text": id_to_doc[doc_id], "rrf_score": rrf_scores[doc_id]}
            for doc_id in sorted_ids
            if doc_id in id_to_doc
        ]


client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

JUDGE_SYSTEM = (
    "You are a relevance judge. Score how relevant the document is to the "
    "query on a scale of 0.0 to 1.0. "
    'Respond with JSON only: {"score": 0.0}'
)


def llm_rerank(query: str, candidates: list[dict], top_k: int = 5) -> list[dict]:
    """Re-rank candidates using Mistral as a relevance judge."""
    scored = []
    for c in candidates:
        try:
            resp = client.chat.completions.create(
                model="mistral",
                messages=[
                    {"role": "system", "content": JUDGE_SYSTEM},
                    {"role": "user", "content": f"Query: {query}\n\nDocument: {c['text'][:500]}"},
                ],
                max_tokens=32,
                temperature=0,
            )
            raw = (resp.choices[0].message.content or "{}").strip()
            raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            score = float(json.loads(raw).get("score", 0.0))
        except Exception:
            score = 0.0  # never crash on a bad judgment
        scored.append({**c, "rerank_score": score})

    return sorted(scored, key=lambda x: x["rerank_score"], reverse=True)[:top_k]


if __name__ == "__main__":
    index = HybridSearchIndex()
    index.add_documents(DOCS, DOC_IDS)

    queries = [
        "FDA approval number 123-456",
        "what are the side effects",
        "serious adverse reactions to the drug",
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
