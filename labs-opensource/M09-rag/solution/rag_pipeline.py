"""
M09 Lab: The Full RAG Pipeline — SOLUTION
==========================================
Run: python rag_pipeline.py   (from this folder; reads ../docs)
"""

import glob
import os

import chromadb
from openai import OpenAI

DOCS_DIR = os.path.join(os.path.dirname(__file__), "..", "docs")


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


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Split text into overlapping chunks, cutting at natural boundaries."""
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]

        if end < len(text):
            # Prefer to cut at a natural boundary in the second half of the window
            for sep in ["\n\n", "\n", ". "]:
                last_sep = chunk.rfind(sep)
                if last_sep > chunk_size * 0.5:
                    end = start + last_sep + len(sep)
                    chunk = text[start:end]
                    break

        chunks.append(chunk.strip())
        start = end - overlap  # overlap for continuity

    return [c for c in chunks if c]


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

    client = chromadb.Client()
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


GROUNDING_SYSTEM = (
    "You are a helpful assistant that answers questions based ONLY on the "
    "provided context. If the context doesn't contain the answer, say "
    "\"I don't have enough information to answer that.\" Always cite your "
    "sources using [Source N] format."
)


def query_rag(collection, question: str, top_k: int = 3, verbose: bool = True) -> str:
    """Retrieve relevant chunks and generate a grounded, cited answer."""
    client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

    try:
        results = collection.query(query_texts=[question], n_results=top_k)
    except Exception as e:
        return f"Retrieval error: {e}"

    if not results["documents"] or not results["documents"][0]:
        return "No relevant documents found. I don't have enough information."

    chunks = results["documents"][0]
    sources = results["metadatas"][0]

    if verbose:
        for i, meta in enumerate(sources):
            print(f"  [retrieved {i + 1}] {meta['source']}: {chunks[i][:60]}...")

    context = "\n\n---\n\n".join(
        f"[Source {i + 1}: {meta['source']}]\n{chunk}"
        for i, (chunk, meta) in enumerate(zip(chunks, sources))
    )

    try:
        response = client.chat.completions.create(
            model="mistral",
            messages=[
                {"role": "system", "content": GROUNDING_SYSTEM},
                {"role": "user", "content": (
                    f"Context:\n{context}\n\n"
                    f"Question: {question}\n\n"
                    "Answer based on the context above, citing sources:"
                )},
            ],
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Generation error: {e}"


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
