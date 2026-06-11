# M10 Lab: Advanced RAG Patterns

> Basic RAG fails on exact identifiers ("FDA approval 123-456") and on vague queries. The fixes: hybrid search (BM25 keyword + dense semantic, merged with Reciprocal Rank Fusion) and re-ranking.

## Prerequisites

- M09 complete
- Dependencies:
  ```bash
  pip install openai chromadb rank-bm25     # Python
  npm install openai                        # Node.js (BM25 implemented by hand)
  ```

> **Scope note:** the Python lab is the full pipeline (BM25 + dense via ChromaDB's built-in embedder + RRF + LLM re-rank). The Node.js lab covers BM25 + LLM re-rank — the dense half needs a Chroma server in JS, so it's a stretch goal there. The course HTML additionally covers semantic chunking, multi-query expansion, and cross-encoder re-rankers; treat those as further stretch material.

## The Corpus

Seven one-line "metformin" documents baked into the lab file — chosen so dense-only retrieval **demonstrably fails** on Q1 (exact FDA number) and BM25-only fails on the paraphrased side-effects question. You can see both failure modes, then watch the hybrid fix them.

## Exercises (one file: `hybrid_rag.py` / `.js`)

| Part | What You Build | Key Concept |
|------|---------------|-------------|
| 1 | `rrf(rankings, k=60)` | Reciprocal Rank Fusion — merge ranked lists without comparing incomparable scores |
| 2 | `HybridSearchIndex.search()` | BM25 top-20 + dense top-20 → RRF → top-k |
| 3 | `llm_rerank()` | Mistral as a 0.0–1.0 relevance judge over the candidates |

### Part 1: RRF

For each ranked list, the doc at rank *r* earns `1 / (k + r)` points; sum across lists. `k=60` is the well-validated default — it stops a single rank-1 hit from dominating. **No score normalization needed** — that's the whole point of RRF: it only uses ranks, so BM25 scores and cosine distances never have to be compared directly.

### Part 2: Hybrid Search

1. BM25: `bm25.get_scores(query.lower().split())` → take top `fetch_k=20` doc IDs by score
2. Dense: `collection.query(query_texts=[query], n_results=20)` → IDs already sorted
3. `rrf([bm25_ranked, dense_ranked])` → sort → top_k result objects

### Part 3: LLM Re-rank

For each candidate, ask Mistral (temperature 0, `max_tokens=32`): *"Score how relevant the document is to the query on a scale of 0.0 to 1.0. Respond with JSON only: {"score": 0.0}"*. Parse defensively — strip markdown fences, default to 0.0 on any error. Sort by score.

**Why LLM instead of a cross-encoder?** No extra model download, and Mistral can apply domain logic. The cost: one Ollama call per candidate (~1-3s each). Production answer: cross-encoder for speed, LLM for specialized domains.

## Run It

```bash
python starter/hybrid_rag.py
```

The harness runs 3 queries through BM25-only, dense-only, and hybrid, printing rank tables — then re-ranks the hybrid candidates with the LLM judge.

**The result that matters:** "FDA approval number 123-456" — dense-only usually ranks the right doc low or misses it (embeddings blur exact identifiers); BM25 nails it; hybrid gets it right *while also* handling the paraphrased queries BM25 fumbles.

## Stretch Goals

- Swap the LLM re-ranker for `cross-encoder/ms-marco-MiniLM-L-6-v2` (`pip install sentence-transformers`) and compare latency
- Implement multi-query expansion: ask Mistral for 3 rephrasings, retrieve for each, RRF-merge all lists
- Port your M09 UCC corpus into this pipeline and re-run the M09 questions
