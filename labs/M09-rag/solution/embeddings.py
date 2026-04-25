"""
M09 Lab — Step 2: Embeddings & Vector Store (SOLUTION)
=======================================================
Embed document chunks and store them in ChromaDB for similarity search.

Run:
    python solution/embeddings.py
"""

import os
import sys

import chromadb

sys.path.insert(0, os.path.dirname(__file__))
from chunker import load_documents, chunk_by_headers  # noqa: E402


# ---------------------------------------------------------------------------
# ChromaDB Setup
# ---------------------------------------------------------------------------

def get_chroma_client() -> chromadb.ClientAPI:
    """Create an ephemeral (in-memory) ChromaDB client."""
    return chromadb.Client()


# ---------------------------------------------------------------------------
# Create Collection and Add Chunks
# ---------------------------------------------------------------------------

def create_collection(
    client: chromadb.ClientAPI,
    chunks: list[dict],
    collection_name: str = "ucc_documents",
) -> chromadb.Collection:
    """
    Create a ChromaDB collection and add all chunks to it.
    ChromaDB automatically embeds documents using its default embedding function.
    """
    collection = client.get_or_create_collection(name=collection_name)

    documents = [chunk["text"] for chunk in chunks]
    metadatas = [chunk["metadata"] for chunk in chunks]
    ids = [f"chunk_{i}" for i in range(len(chunks))]

    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids,
    )

    return collection


# ---------------------------------------------------------------------------
# Search the Collection
# ---------------------------------------------------------------------------

def search(
    collection: chromadb.Collection,
    query: str,
    n_results: int = 3,
) -> dict:
    """Search the collection for chunks most similar to the query."""
    results = collection.query(
        query_texts=[query],
        n_results=n_results,
    )
    return results


# ---------------------------------------------------------------------------
# Display Helper
# ---------------------------------------------------------------------------

def print_results(query: str, results: dict):
    """Pretty-print search results."""
    print(f"\n{'─' * 60}")
    print(f"Query: \"{query}\"")
    print(f"{'─' * 60}")

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    for i, (doc, meta, dist) in enumerate(zip(documents, metadatas, distances)):
        print(f"\n  Result {i + 1} (distance: {dist:.4f}):")
        print(f"  Source : {meta.get('source', 'unknown')}")
        print(f"  Header : {meta.get('header', 'N/A')}")
        print(f"  Preview: {doc[:150].strip()}...")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    docs_dir = os.path.join(os.path.dirname(__file__), "..", "docs")

    print("=" * 60)
    print("Loading and chunking documents...")
    print("=" * 60)
    documents = load_documents(docs_dir)
    all_chunks = []
    for doc in documents:
        chunks = chunk_by_headers(doc["content"], filename=doc["filename"])
        all_chunks.extend(chunks)
    print(f"\nTotal chunks: {len(all_chunks)}")

    print("\n" + "=" * 60)
    print("Creating ChromaDB collection...")
    print("=" * 60)
    client = get_chroma_client()
    collection = create_collection(client, all_chunks)
    print(f"  Collection '{collection.name}' created with {collection.count()} chunks.")

    print("\n" + "=" * 60)
    print("Running similarity searches...")
    print("=" * 60)

    test_queries = [
        "What is perfection in UCC Article 9?",
        "How do I search for liens on a business?",
        "What types of collateral can be secured?",
        "When does a UCC filing expire?",
    ]

    for query in test_queries:
        results = search(collection, query, n_results=3)
        print_results(query, results)

    print("\n" + "=" * 60)
    print("Done! Your vector store is working.")
    print("=" * 60)


if __name__ == "__main__":
    main()
