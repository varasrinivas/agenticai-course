# M10: Advanced RAG Patterns

**Track**: 3 — Memory & Context | **Position**: 10 of 30 | **Level**: Advanced
**Prerequisites**: M09
**Estimated Time**: 60-75 minutes
**Track Color**: var(--track-memory) / #06B6D4

## Concepts
- Naive RAG vs Advanced RAG (visual comparison)
- Hybrid search: keyword (BM25) + semantic (vector) — animated fusion
- Re-ranking: why retrieval order matters (animated re-ranking pipeline)
- Query transformation: HyDE, multi-query, step-back prompting
- Contextual compression — trimming retrieved chunks to relevant sentences
- RAG evaluation: precision, recall, faithfulness metrics

## Hands-On Lab
Upgrade the M09 RAG system with hybrid search (BM25 + vector) and re-ranking. Compare naive vs advanced RAG on the same 10 UCC domain questions. Measure precision/recall improvement.

## Quiz Focus (5 questions)
1. What does hybrid search combine? (keyword BM25 + semantic vector search)
2. Is hybrid search always better? (no — adds latency, sometimes keyword alone is better for exact matches)
3. What does re-ranking do? (reorders retrieved chunks by relevance using a cross-encoder)
4. What is HyDE? (Hypothetical Document Embeddings — generate a fake answer, embed that instead of the question)
5. How do you measure RAG quality? (retrieval precision/recall + generation faithfulness)
