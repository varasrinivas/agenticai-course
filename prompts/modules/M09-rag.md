# M09: RAG — Retrieval-Augmented Generation

**Track**: 3 — Memory & Context | **Position**: 9 of 30 | **Level**: Intermediate
**Prerequisites**: M01-M04, M08
**Estimated Time**: 75-90 minutes
**Track Color**: var(--track-memory) / #06B6D4

## Concepts
- The knowledge problem: Claude's training cutoff and domain gaps
- RAG pipeline: Document loading → Chunking → Embedding → Storage → Retrieval → Generation
- Embeddings explained: "words as coordinates in meaning-space" (interactive 3D visualization)
- Cosine similarity — animated vector comparison
- Chunking strategies: fixed-size, semantic, recursive (visual comparison)
- Vector databases: ChromaDB, Pinecone, pgvector (animated index lookup)
- Visual: Animated embedding space with query vector finding nearest neighbors

## Hands-On Lab
Build a "Chat with your docs" RAG system using UCC Article 9 reference documents. Ingest 4 markdown docs into ChromaDB, build retrieval pipeline, generate cited responses.

## Quiz Focus (5 questions)
1. Is RAG the same as fine-tuning? (no — RAG doesn't change the model)
2. What are embeddings? (numerical representations of meaning)
3. Why chunk documents? (embedding models have token limits, smaller chunks = more precise retrieval)
4. Does RAG eliminate hallucinations? (no — reduces them but doesn't eliminate)
5. What does cosine similarity measure? (how close two vectors are in meaning-space)
