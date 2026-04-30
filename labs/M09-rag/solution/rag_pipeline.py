"""
M09 Lab — Step 3: Full RAG Pipeline (SOLUTION)
================================================
Retrieve relevant chunks from the vector store, then generate
answers with citations using Claude.

Run:
    python solution/rag_pipeline.py
"""

import os
import sys

import anthropic
import chromadb
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(__file__))
from chunker import load_documents, chunk_by_headers  # noqa: E402
from embeddings import get_chroma_client, create_collection, search  # noqa: E402


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

def build_vector_store() -> chromadb.Collection:
    """Load docs, chunk them, and build the vector store."""
    docs_dir = os.path.join(os.path.dirname(__file__), "..", "docs")
    documents = load_documents(docs_dir)

    all_chunks = []
    for doc in documents:
        chunks = chunk_by_headers(doc["content"], filename=doc["filename"])
        all_chunks.extend(chunks)

    client = get_chroma_client()
    collection = create_collection(client, all_chunks)
    print(f"Vector store ready: {collection.count()} chunks indexed.\n")
    return collection


# ---------------------------------------------------------------------------
# Retrieve Relevant Chunks
# ---------------------------------------------------------------------------

def retrieve(
    collection: chromadb.Collection,
    query: str,
    n_results: int = 3,
) -> list[dict]:
    """Retrieve the most relevant chunks for a query."""
    results = search(collection, query, n_results)

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    chunks = []
    for doc, meta, dist in zip(documents, metadatas, distances):
        chunks.append({
            "text": doc,
            "source": meta.get("source", "unknown"),
            "header": meta.get("header", "N/A"),
            "distance": dist,
        })

    return chunks


# ---------------------------------------------------------------------------
# Generate Answer with Citations
# ---------------------------------------------------------------------------

RAG_SYSTEM_PROMPT = """You are a helpful assistant that answers questions about UCC \
(Uniform Commercial Code) filings and secured transactions.

Answer the question based ONLY on the provided context. \
Cite your sources using [Source: filename] format. \
If the context doesn't contain enough information to answer the question, say so clearly."""


def generate(query: str, context_chunks: list[dict]) -> str:
    """Send the query and retrieved context to Claude to generate an answer."""
    # Build context string
    context_parts = []
    for chunk in context_chunks:
        context_parts.append(
            f"[Source: {chunk['source']} | Section: {chunk['header']}]\n"
            f"{chunk['text']}"
        )
    context_str = "\n\n".join(context_parts)

    # Build user message
    user_message = f"""Context:
---
{context_str}
---

Question: {query}"""

    # Call Claude
    client = anthropic.Anthropic()
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=RAG_SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": user_message},
        ],
    )

    return message.content[0].text


# ---------------------------------------------------------------------------
# End-to-End RAG Query
# ---------------------------------------------------------------------------

def rag_query(collection: chromadb.Collection, query: str) -> str:
    """End-to-end RAG: retrieve relevant chunks, then generate an answer."""
    # Retrieve
    chunks = retrieve(collection, query)

    # Show sources
    print("\n  Sources retrieved:")
    for i, chunk in enumerate(chunks):
        print(f"    {i + 1}. {chunk['source']} — {chunk['header']} (distance: {chunk['distance']:.4f})")

    # Generate
    answer = generate(query, chunks)
    return answer


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("M09 Lab — Full RAG Pipeline")
    print("=" * 60)

    print("\nBuilding vector store...")
    collection = build_vector_store()

    test_queries = [
        "What is the difference between a UCC-1 and UCC-3 filing?",
        "What are the priority rules for secured transactions?",
        "How should I interpret multiple liens on the same debtor?",
        "What is a blanket lien and why is it a red flag?",
    ]

    for query in test_queries:
        print("\n" + "=" * 60)
        print(f"Question: {query}")
        print("=" * 60)

        answer = rag_query(collection, query)
        print(f"\nAnswer:\n{answer}")

    print("\n" + "=" * 60)
    print("RAG pipeline complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
