"""
M09 Lab: The Full RAG Pipeline
===============================
Load → chunk → store → retrieve → generate-with-citations.
Run: python rag_pipeline.py   (from this folder; reads ../docs)
Requires: pip install openai "chromadb>=0.4.0"
"""

import glob
import os

import chromadb
from openai import OpenAI

DOCS_DIR = os.path.join(os.path.dirname(__file__), "..", "docs")


# ── Document Loading (COMPLETE) ──────────────────────────────
def load_documents(docs_dir: str) -> list[dict]:
    """Load all .md and .txt files from a directory."""
    docs = []
    for pattern in ["*.md", "*.txt"]:
        for path in glob.glob(os.path.join(docs_dir, pattern)):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    docs.append({"content": f.read(), "source": os.path.basename(path)})
            except (IOError, UnicodeDecodeError) as e:
                print(f"  Skipping {path}: {e}")
    if not docs:
        raise FileNotFoundError(f"No documents found in {docs_dir}")
    return docs


# ── Part 1: Chunking (YOUR JOB) ──────────────────────────────
def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Split text into overlapping chunks, cutting at natural boundaries.

    TODO:
    1. If len(text) <= chunk_size: return [text]
    2. Walk the text with a start pointer:
       a. end = start + chunk_size; chunk = text[start:end]
       b. If end < len(text): try separators ["\\n\\n", "\\n", ". "] in order —
          find the LAST occurrence (rfind) of the separator inside chunk;
          if it sits past the halfway point (last_sep > chunk_size * 0.5),
          cut there instead: end = start + last_sep + len(sep), re-slice chunk,
          and stop trying further separators
       c. Append chunk.strip()
       d. start = end - overlap     ← overlap for continuity
    3. Return chunks, dropping any empty strings
    """
    pass  # Remove this line when you add your code


# ── Part 2: Ingestion (COMPLETE) ─────────────────────────────
def ingest(docs_dir: str = DOCS_DIR) -> chromadb.Collection:
    """Load docs, chunk them, and store in ChromaDB."""
    print("-- Ingestion Pipeline --")
    docs = load_documents(docs_dir)
    print(f"  Loaded {len(docs)} documents")

    all_chunks = []
    for doc in docs:
        for i, chunk in enumerate(chunk_text(doc["content"], chunk_size=500, overlap=50)):
            all_chunks.append({"text": chunk, "source": doc["source"], "index": i})
    print(f"  Created {len(all_chunks)} chunks")

    # ChromaDB embeds with its built-in model — no embedding API needed
    client = chromadb.Client()  # in-memory; PersistentClient(path=...) for disk
    collection = client.get_or_create_collection(
        name="rag_lab", metadata={"hnsw:space": "cosine"}
    )
    collection.add(
        ids=[f"chunk_{i}" for i in range(len(all_chunks))],
        documents=[c["text"] for c in all_chunks],
        metadatas=[{"source": c["source"], "index": c["index"]} for c in all_chunks],
    )
    print(f"  Stored {collection.count()} chunks in ChromaDB")
    return collection


# ── Part 3: Query (YOUR JOB) ─────────────────────────────────
GROUNDING_SYSTEM = (
    "You are a helpful assistant that answers questions based ONLY on the "
    "provided context. If the context doesn't contain the answer, say "
    "\"I don't have enough information to answer that.\" Always cite your "
    "sources using [Source N] format."
)


def query_rag(collection, question: str, top_k: int = 3, verbose: bool = True) -> str:
    """Retrieve relevant chunks and generate a grounded, cited answer.

    TODO:
    1. results = collection.query(query_texts=[question], n_results=top_k)
       (try/except → return f"Retrieval error: {e}")
    2. If not results["documents"] or not results["documents"][0]:
         return "No relevant documents found. I don't have enough information."
    3. chunks = results["documents"][0]; sources = results["metadatas"][0]
       If verbose: print each retrieved source + first 60 chars
    4. Build the context block:
         f"[Source {i+1}: {meta['source']}]\\n{chunk}"  joined by "\\n\\n---\\n\\n"
    5. Call Mistral with GROUNDING_SYSTEM as the system message and a user
       message: f"Context:\\n{context}\\n\\nQuestion: {question}\\n\\n
                  Answer based on the context above, citing sources:"
       (try/except → return f"Generation error: {e}")
    6. Return the answer text
    """
    pass  # Remove this line when you add your code


# ── Test harness (COMPLETE) ──────────────────────────────────
if __name__ == "__main__":
    collection = ingest()

    questions = [
        "What happens if a continuation statement is filed late?",
        "What are the high-risk indicators in a lien risk assessment?",
        "What is the capital of France?",  # NOT in the docs — must refuse!
    ]
    for q in questions:
        print(f"\n{'=' * 60}\nQ: {q}")
        print(f"A: {query_rag(collection, q)}")
