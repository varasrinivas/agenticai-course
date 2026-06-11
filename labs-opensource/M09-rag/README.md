# M09 Lab: RAG — Retrieval-Augmented Generation

> Stop hoping the model knows your documents; SHOW it the right ones. You'll build the full pipeline: load → chunk → embed → store → retrieve → generate-with-citations, against a small UCC-filings knowledge base (Domain C).

## Prerequisites

- M01 complete
- Dependencies:
  ```bash
  pip install openai "chromadb>=0.4.0"      # Python
  npm install openai chromadb               # Node.js — see note below
  ```

> **Node.js note:** the `chromadb` JS client talks to a Chroma **server** (it has no in-process mode). Start one first: `pip install chromadb && chroma run --path ./chroma_data`. The Python lab runs fully in-process — if you only do one language here, do Python.

## The Knowledge Base

`docs/` contains three small files about UCC filings (the course's Domain C):
- `ucc_filing_guide.md` — UCC-1 filings, continuations, amendments
- `risk_criteria.md` — high/medium/low lien-risk indicators
- `faq.md` — Q&A about terminations and UCC-3s

Small on purpose: you can verify every retrieval by eye.

## Exercises (one file: `rag_pipeline.py` / `.js`)

| Part | Function | What You Build |
|------|----------|---------------|
| 1 | `chunk_text()` | Overlapping splitter that prefers natural boundaries |
| 2 | `ingest()` | (Complete) Load → chunk → store in ChromaDB |
| 3 | `query_rag()` | Retrieve top-k → build cited context → generate grounded answer |

### Part 1: `chunk_text(text, chunk_size=500, overlap=50)`

- If the text fits in one chunk, return it as-is
- Otherwise walk forward `chunk_size` at a time, but **prefer to cut at a separator** (`"\n\n"`, `"\n"`, `". "`) found in the second half of the window — never mid-sentence if avoidable
- Each next chunk starts `overlap` chars before the previous end (continuity across boundaries)

### Part 3: `query_rag(collection, question, top_k=3)`

1. `collection.query(query_texts=[question], n_results=top_k)` — ChromaDB embeds the question with its built-in model; no embedding API needed
2. If nothing comes back: return "I don't have enough information" — **a grounded "I don't know" beats a confident hallucination**
3. Build the context block: `[Source N: filename]\n{chunk}` joined by `---` separators
4. Ask Mistral with a system prompt that forbids answering outside the context and requires `[Source N]` citations

## Run It

```bash
python starter/rag_pipeline.py
```

The harness ingests `docs/`, then asks three questions:
1. *"What happens if a continuation statement is filed late?"* → should cite the FAQ
2. *"What are high-risk lien indicators?"* → should cite risk_criteria.md
3. *"What is the capital of France?"* → should REFUSE (not in the docs!)

Question 3 is the real test. If your pipeline answers it, your system prompt isn't grounding hard enough.

## Stretch Goals

- Print the cosine distances and add a relevance threshold (reject chunks with distance > 0.6)
- Swap ChromaDB's default embedder for `sentence-transformers` (`all-MiniLM-L6-v2`) and compare retrieval quality
- Use `chromadb.PersistentClient(path="./chroma_data")` so ingestion survives restarts
