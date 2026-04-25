"""
M09 Lab — Step 2: Embeddings & Vector Store
============================================
Embed document chunks and store them in ChromaDB for similarity search.

Uses ChromaDB's default embedding function (all-MiniLM-L6-v2 via
sentence-transformers) so no external API key is needed for embeddings.

Run:
    python starter/embeddings.py
"""

import os
import sys

import chromadb

# Import our chunker from Step 1
sys.path.insert(0, os.path.dirname(__file__))
from chunker import load_documents, chunk_by_headers  # noqa: E402


# ---------------------------------------------------------------------------
# ChromaDB Setup (COMPLETE — no changes needed)
# ---------------------------------------------------------------------------

def get_chroma_client() -> chromadb.ClientAPI:
    """Create an ephemeral (in-memory) ChromaDB client."""
    return chromadb.Client()


# ---------------------------------------------------------------------------
# TODO 1: Create Collection and Add Chunks
# ---------------------------------------------------------------------------

def create_collection(
    client: chromadb.ClientAPI,
    chunks: list[dict],
    collection_name: str = "ucc_documents",
) -> chromadb.Collection:
    """
    Create a ChromaDB collection and add all chunks to it.

    Each chunk dict looks like:
      {
        "text": "chunk text...",
        "metadata": {"source": "file.md", "header": "Section", "chunk_index": 0}
      }

    Steps:
      1. Create (or get) a collection with the given name.
      2. Prepare three parallel lists:
         - documents: the chunk text strings
         - metadatas: the chunk metadata dicts
         - ids: unique string IDs (e.g., "chunk_0", "chunk_1", ...)
      3. Add them to the collection using collection.add().
      4. Return the collection.

    ChromaDB will automatically embed the documents using its default
    embedding function (sentence-transformers/all-MiniLM-L6-v2).

    Args:
        client: ChromaDB client
        chunks: list of chunk dicts from the chunker
        collection_name: name for the collection

    Returns:
        The ChromaDB collection with all chunks added.
    """
    # TODO: Implement collection creation and chunk insertion.
    # Hint:
    #   collection = client.get_or_create_collection(name=collection_name)
    #   collection.add(documents=[...], metadatas=[...], ids=[...])
    pass


# ---------------------------------------------------------------------------
# TODO 2: Search the Collection
# ---------------------------------------------------------------------------

def search(
    collection: chromadb.Collection,
    query: str,
    n_results: int = 3,
) -> dict:
    """
    Search the collection for chunks most similar to the query.

    Steps:
      1. Use collection.query() with query_texts=[query] and n_results.
      2. Return the raw results dict.

    The results dict contains:
      - results["documents"][0]   -> list of matching document texts
      - results["metadatas"][0]   -> list of metadata dicts
      - results["distances"][0]   -> list of distance scores (lower = more similar)
      - results["ids"][0]         -> list of chunk IDs

    Args:
        collection: The ChromaDB collection to search
        query: The search query string
        n_results: Number of results to return

    Returns:
        The ChromaDB query results dict.
    """
    # TODO: Implement similarity search.
    # Hint: results = collection.query(query_texts=[query], n_results=n_results)
    pass


# ---------------------------------------------------------------------------
# Display Helper (COMPLETE — no changes needed)
# ---------------------------------------------------------------------------

def print_results(query: str, results: dict):
    """Pretty-print search results."""
    print(f"\n{'─' * 60}")
    print(f"Query: \"{query}\"")
    print(f"{'─' * 60}")

    if results is None:
        print("  *** search() returned None — implement TODO 2 ***")
        return

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    for i, (doc, meta, dist) in enumerate(zip(documents, metadatas, distances)):
        print(f"\n  Result {i + 1} (distance: {dist:.4f}):")
        print(f"  Source : {meta.get('source', 'unknown')}")
        print(f"  Header : {meta.get('header', 'N/A')}")
        print(f"  Preview: {doc[:150].strip()}...")


# ---------------------------------------------------------------------------
# Main — Test Your Implementation
# ---------------------------------------------------------------------------

def main():
    docs_dir = os.path.join(os.path.dirname(__file__), "..", "docs")

    # --- Load and chunk documents ---
    print("=" * 60)
    print("Loading and chunking documents...")
    print("=" * 60)
    documents = load_documents(docs_dir)
    all_chunks = []
    for doc in documents:
        chunks = chunk_by_headers(doc["content"], filename=doc["filename"])
        if chunks:
            all_chunks.extend(chunks)
    print(f"\nTotal chunks: {len(all_chunks)}")

    if not all_chunks:
        print("\nERROR: No chunks produced. Complete Step 1 (chunker.py) first!")
        return

    # --- Create collection ---
    print("\n" + "=" * 60)
    print("Creating ChromaDB collection...")
    print("=" * 60)
    client = get_chroma_client()
    collection = create_collection(client, all_chunks)

    if collection is None:
        print("\n  *** create_collection() returned None — implement TODO 1 ***")
        return

    print(f"  Collection '{collection.name}' created with {collection.count()} chunks.")

    # --- Run test queries ---
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
