# M09 Lab: RAG — Retrieval-Augmented Generation

> Claude knows a lot — but it doesn't know YOUR data. RAG fixes that.

In this lab you'll build a complete "Chat with your docs" RAG system using real UCC (Uniform Commercial Code) Article 9 reference documents. You'll go through the full pipeline: document loading, chunking, embedding, vector storage, retrieval, and generation with citations.

## Prerequisites

- Python 3.10+ or Node.js 18+
- Anthropic API key in `.env` file (`ANTHROPIC_API_KEY=sk-ant-...`)
- Install dependencies:
  ```bash
  # Python
  pip install anthropic chromadb python-dotenv

  # Node.js
  npm install @anthropic-ai/sdk chromadb dotenv
  ```
- For Python: ChromaDB will automatically download the `all-MiniLM-L6-v2` sentence-transformer model on first run (~80MB). This is used for local embeddings — no embedding API key needed.
- For Node.js: Start a local ChromaDB server before running Steps 2 and 3:
  ```bash
  pip install chromadb
  chroma run --path ./chroma_data
  ```

## Reference Documents

The `docs/` folder contains 4 UCC reference documents that serve as your knowledge base:

| File | Topic | Size |
|------|-------|------|
| `ucc-article-9-overview.md` | Overview of secured transactions | ~800 words |
| `ucc-filing-types.md` | Guide to UCC-1, UCC-3, UCC-5 filings | ~600 words |
| `collateral-types.md` | Collateral classification (goods, intangibles, etc.) | ~700 words |
| `lien-search-guide.md` | How to conduct a UCC lien search | ~600 words |

These documents are realistic and educational — you'll learn real UCC concepts as you build!

## Exercises

| Step | Files | What You Build | Key Concept |
|------|-------|---------------|-------------|
| 1 | `chunker.py` / `chunker.js` | Document loader + chunker | Chunking strategies, overlap, metadata |
| 2 | `embeddings.py` / `embeddings.js` | Embedding + vector store | Embeddings, cosine similarity, ChromaDB |
| 3 | `rag_pipeline.py` / `rag_pipeline.js` | Full RAG pipeline | End-to-end RAG, citations, faithfulness |

## Step 1: Document Loading & Chunking

**File:** `starter/chunker.py` (or `chunker.js`)

You will implement two chunking strategies:

1. **Fixed-size chunking** (`chunk_document`) — Split text into overlapping character-based chunks. You control the chunk size and overlap.
2. **Header-based semantic chunking** (`chunk_by_headers`) — Split on `##` markdown headers so each chunk corresponds to a meaningful section.
3. **Metadata wrapper** (`chunk_with_metadata`) — Attach source filename, chunk index, and method info to each chunk.

**What to implement:**
- `chunk_document(text, chunk_size=500, overlap=50)` — sliding window with overlap
- `chunk_by_headers(text, filename)` — split on `## ` headings, capture header as metadata
- `chunk_with_metadata(text, filename, chunk_size, overlap)` — wraps fixed-size chunks with metadata

**Run it:**
```bash
python starter/chunker.py
# or
node starter/chunker.js
```

**You'll see:** Chunk counts and sizes for both strategies — header-based chunking produces fewer, more meaningful chunks.

## Step 2: Embeddings & Vector Store

**File:** `starter/embeddings.py` (or `embeddings.js`)

You will build a vector store using ChromaDB:

1. **Create a collection** (`create_collection`) — Add all document chunks to a ChromaDB collection with metadata. ChromaDB handles embedding automatically.
2. **Similarity search** (`search`) — Query the collection and get the top-N most relevant chunks.

**What to implement:**
- `create_collection(client, chunks)` — prepare documents, metadatas, and IDs arrays, then add to collection
- `search(collection, query, n_results=3)` — query the collection by text similarity

**Test queries:**
- "What is perfection in UCC Article 9?"
- "How do I search for liens on a business?"
- "What types of collateral can be secured?"
- "When does a UCC filing expire?"

**Run it:**
```bash
python starter/embeddings.py
# or
node starter/embeddings.js
```

**You'll see:** For each query, the top 3 most similar chunks with distance scores and source metadata.

## Step 3: Full RAG Pipeline

**File:** `starter/rag_pipeline.py` (or `rag_pipeline.js`)

You will build the complete retrieve-then-generate pipeline:

1. **Retrieve** (`retrieve`) — Use Step 2's vector store to find relevant chunks for a question.
2. **Generate** (`generate`) — Send the question + retrieved context to Claude with a RAG system prompt that enforces citations.
3. **End-to-end** (`rag_query`) — Wire retrieve and generate together.

**The RAG system prompt:**
```
You are a helpful assistant that answers questions about UCC filings and secured transactions.
Answer the question based ONLY on the provided context.
Cite your sources using [Source: filename] format.
If the context doesn't contain enough information, say so clearly.
```

**Test queries:**
- "What is the difference between a UCC-1 and UCC-3 filing?"
- "What are the priority rules for secured transactions?"
- "How should I interpret multiple liens on the same debtor?"
- "What is a blanket lien and why is it a red flag?"

**Run it:**
```bash
python starter/rag_pipeline.py
# or
node starter/rag_pipeline.js
```

**You'll see:** For each question, the retrieved sources and a Claude-generated answer with `[Source: filename]` citations.

## Verification

After completing all three steps, verify:

- [ ] **Step 1:** Chunker loads 4 documents, produces both fixed-size and header-based chunks
- [ ] **Step 1:** Fixed-size chunks have correct overlap (compare end of chunk N with start of chunk N+1)
- [ ] **Step 1:** Header chunks contain the `##` heading text and correct source metadata
- [ ] **Step 2:** ChromaDB collection contains all chunks (check `collection.count()`)
- [ ] **Step 2:** Search results are semantically relevant (the "perfection" query should return the Perfection section)
- [ ] **Step 3:** RAG answers include `[Source: filename]` citations
- [ ] **Step 3:** Answers are grounded in the retrieved context (not hallucinated)
- [ ] **Step 3:** When asked about something not in the docs, the system says so

## What You Built

By completing this lab, you built a full RAG pipeline:

```
User Question
     |
     v
[1. RETRIEVE] — Embed the question, search the vector store
     |
     v
[2. CONTEXT]  — Top-K relevant document chunks
     |
     v
[3. GENERATE] — Send question + context to Claude
     |
     v
Grounded Answer with Citations
```

**Key takeaways:**
- **Chunking matters.** Semantic (header-based) chunks preserve meaning better than fixed-size. The right chunk size balances context and precision.
- **Embeddings enable semantic search.** Unlike keyword search, vector similarity finds conceptually related content even when the words differ.
- **The system prompt is critical.** Instructing Claude to cite sources and stay grounded prevents hallucination.
- **Metadata is essential.** Tracking source files and section headers enables citations and debuggability.

## Next

In **M10**, you'll learn about **memory and context management** — how to handle conversations that exceed the context window, summarization strategies, and when to use RAG vs. long context.
