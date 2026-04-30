"""
M09 Lab — Step 3: Full RAG Pipeline
=====================================
Retrieve relevant chunks from the vector store, then generate
answers with citations using Claude.

Run:
    python starter/rag_pipeline.py
"""

import os
import sys

import anthropic
import chromadb
from dotenv import load_dotenv

load_dotenv()

# Import helpers from previous steps
sys.path.insert(0, os.path.dirname(__file__))
from chunker import load_documents, chunk_by_headers  # noqa: E402
from embeddings import get_chroma_client, create_collection, search  # noqa: E402


# ---------------------------------------------------------------------------
# Setup (COMPLETE — no changes needed)
# ---------------------------------------------------------------------------

def build_vector_store() -> chromadb.Collection:
    """Load docs, chunk them, and build the vector store."""
    docs_dir = os.path.join(os.path.dirname(__file__), "..", "docs")
    documents = load_documents(docs_dir)

    all_chunks = []
    for doc in documents:
        chunks = chunk_by_headers(doc["content"], filename=doc["filename"])
        if chunks:
            all_chunks.extend(chunks)

    if not all_chunks:
        raise RuntimeError("No chunks produced. Complete Steps 1 & 2 first!")

    client = get_chroma_client()
    collection = create_collection(client, all_chunks)

    if collection is None:
        raise RuntimeError("create_collection() returned None. Complete Step 2 first!")

    print(f"Vector store ready: {collection.count()} chunks indexed.\n")
    return collection


# ---------------------------------------------------------------------------
# TODO 1: Retrieve Relevant Chunks
# ---------------------------------------------------------------------------

def retrieve(
    collection: chromadb.Collection,
    query: str,
    n_results: int = 3,
) -> list[dict]:
    """
    Retrieve the most relevant chunks for a query.

    Steps:
      1. Use the search() function from Step 2 to query the collection.
      2. Transform the results into a list of dicts, each containing:
         - "text": the chunk text
         - "source": the source filename from metadata
         - "header": the section header from metadata
         - "distance": the similarity distance score

    Args:
        collection: The ChromaDB collection
        query: The user's question
        n_results: Number of chunks to retrieve

    Returns:
        List of dicts with keys: text, source, header, distance
    """
    # TODO: Implement retrieval.
    # Hint:
    #   results = search(collection, query, n_results)
    #   Then unpack results["documents"][0], results["metadatas"][0],
    #   and results["distances"][0] into a list of dicts.
    pass


# ---------------------------------------------------------------------------
# TODO 2: Generate Answer with Citations
# ---------------------------------------------------------------------------

def generate(query: str, context_chunks: list[dict]) -> str:
    """
    Send the query and retrieved context to Claude to generate an answer.

    Steps:
      1. Build a context string from the retrieved chunks. For each chunk,
         include the source filename and header so Claude can cite them.
         Format each chunk like:
           [Source: filename | Section: header]
           chunk text...

      2. Create the system prompt:
         "You are a helpful assistant that answers questions about UCC
         (Uniform Commercial Code) filings and secured transactions.
         Answer the question based ONLY on the provided context.
         Cite your sources using [Source: filename] format.
         If the context doesn't contain enough information to answer
         the question, say so clearly."

      3. Send the message to Claude using the Anthropic SDK:
         - model: "claude-sonnet-4-6"
         - max_tokens: 1024
         - system: your system prompt
         - messages: one user message containing the context + query

      4. Return Claude's response text.

    The user message should be formatted like:
      Context:
      ---
      [Source: file.md | Section: Header]
      chunk text...

      [Source: file2.md | Section: Header2]
      chunk text...
      ---

      Question: {query}

    Args:
        query: The user's question
        context_chunks: List of chunk dicts from retrieve()

    Returns:
        Claude's answer as a string.
    """
    # TODO: Implement the generation step.
    # Hint:
    #   client = anthropic.Anthropic()
    #   message = client.messages.create(...)
    #   return message.content[0].text
    pass


# ---------------------------------------------------------------------------
# TODO 3: End-to-End RAG Query
# ---------------------------------------------------------------------------

def rag_query(collection: chromadb.Collection, query: str) -> str:
    """
    End-to-end RAG: retrieve relevant chunks, then generate an answer.

    Steps:
      1. Call retrieve() to get relevant chunks.
      2. Call generate() with the query and chunks.
      3. Print the sources used.
      4. Return the generated answer.

    Args:
        collection: The ChromaDB collection
        query: The user's question

    Returns:
        The generated answer string.
    """
    # TODO: Implement the end-to-end pipeline.
    # Hint:
    #   chunks = retrieve(collection, query)
    #   answer = generate(query, chunks)
    #   Print which sources were used.
    #   Return the answer.
    pass


# ---------------------------------------------------------------------------
# Main — Test Your Implementation
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("M09 Lab — Full RAG Pipeline")
    print("=" * 60)

    # Build the vector store
    print("\nBuilding vector store...")
    collection = build_vector_store()

    # Test queries
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

        if answer:
            print(f"\nAnswer:\n{answer}")
        else:
            print("\n  *** rag_query() returned None — implement TODOs 1-3 ***")

    print("\n" + "=" * 60)
    print("RAG pipeline complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
