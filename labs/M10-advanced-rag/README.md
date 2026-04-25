# M10 Lab: Advanced RAG Patterns

> Naive RAG gets you 60% of the way. These patterns get you to 90%.

## Prerequisites

- Python 3.10+ or Node.js 18+
- Anthropic API key in `.env` file (`ANTHROPIC_API_KEY=sk-ant-...`)
- Completed M09 lab (we reuse its document corpus from `../M09-rag/docs/`)
- Install dependencies:
  ```bash
  # Python
  pip install anthropic python-dotenv chromadb rank-bm25

  # Node.js
  npm install @anthropic-ai/sdk dotenv chromadb
  ```

## Exercises

| Step | File | What You Build | Key Concept |
|------|------|---------------|-------------|
| 1 | `hybrid_search.py` / `hybrid_search.js` | Hybrid search combining BM25 keyword + vector semantic search | BM25 scoring, reciprocal rank fusion, keyword vs semantic tradeoffs |
| 2 | `reranker.py` / `reranker.js` | Re-ranking pipeline -- retrieve broadly, re-rank with Claude | Cross-encoder re-ranking, relevance scoring, precision improvement |
| 3 | `advanced_rag.py` / `advanced_rag.js` | Full advanced RAG with query transformation + hybrid search + re-ranking | HyDE, multi-query, complete pipeline comparison |

## Step 1: Hybrid Search (BM25 + Vector)

**File:** `starter/hybrid_search.py` (or `.js`)

You will:
1. Build a `BM25Index` class that tokenizes documents, computes term frequency (TF), inverse document frequency (IDF), and BM25 scores
2. Implement `bm25_search(query, top_k=5)` -- keyword-based search
3. Use the provided `vector_search(query, collection, top_k=5)` -- semantic search via ChromaDB
4. Implement `hybrid_search(query, bm25_results, vector_results, alpha=0.5)` -- reciprocal rank fusion combining both result sets
5. Compare results across 5 queries where keyword and semantic search disagree

**Test queries:**
- `"UCC-3 amendment"` -- keyword wins (exact term match)
- `"How do I protect my loan?"` -- semantic wins (concept match to "perfection")
- `"filing expiration"` -- both work well
- `"What happens when collateral is sold?"` -- semantic wins (concept: proceeds)
- `"Article 9 Section 315"` -- keyword wins (exact reference)

**Run it:**
```bash
python starter/hybrid_search.py
# or
node starter/hybrid_search.js
```

## Step 2: Re-Ranking with Claude

**File:** `starter/reranker.py` (or `.js`)

You will:
1. Use the provided `retrieve_candidates(query, n=10)` to get broad initial results from hybrid search
2. Implement `rerank_with_claude(query, candidates)` -- send each candidate to Claude asking it to rate relevance 0-10 with an explanation
3. Implement `rerank(query, candidates, top_k=3)` -- sort by Claude's relevance score, return top_k
4. Show before/after rankings with Claude's reasoning

**Run it:**
```bash
python starter/reranker.py
# or
node starter/reranker.js
```

## Step 3: Full Advanced RAG Pipeline

**File:** `starter/advanced_rag.py` (or `.js`)

You will:
1. Implement `transform_query_hyde(query)` -- HyDE: ask Claude to write a hypothetical answer, use it for retrieval
2. Implement `transform_query_multi(query)` -- Multi-query: generate 3 search queries from different angles
3. Wire up `advanced_rag_pipeline(query)` -- full pipeline: transform -> hybrid search -> re-rank -> generate
4. Implement `compare_naive_vs_advanced(query)` -- run both pipelines on the same query, show side-by-side results
5. Run 5 UCC domain questions and print a comparison table

**Run it:**
```bash
python starter/advanced_rag.py
# or
node starter/advanced_rag.js
```

## Verification

After completing all three steps, run the solutions to see expected behavior:

```bash
# Python
python solution/hybrid_search.py
python solution/reranker.py
python solution/advanced_rag.py

# Node.js
node solution/hybrid_search.js
node solution/reranker.js
node solution/advanced_rag.js
```

Compare your output against `expected_output/sample_output.txt`.

## What You Built

By completing this lab, you have implemented:

1. **BM25 keyword search** -- the classic information retrieval algorithm that excels at exact term matching
2. **Hybrid search with reciprocal rank fusion** -- combining keyword and semantic search for best-of-both-worlds retrieval
3. **Claude-powered re-ranking** -- using an LLM as a cross-encoder to improve precision after broad retrieval
4. **Query transformation (HyDE + multi-query)** -- rewriting queries to improve retrieval before it happens
5. **A complete advanced RAG pipeline** -- the production pattern: transform -> retrieve (hybrid) -> re-rank -> generate

These patterns are the difference between a demo RAG system and a production RAG system.

## Next

- **M11**: Agents with Memory (Conversation + Persistent State)
- **M12**: Multi-Agent Orchestration
