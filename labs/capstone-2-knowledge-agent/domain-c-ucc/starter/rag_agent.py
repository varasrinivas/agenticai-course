"""
RAG Agent — Capstone 2, Domain C (UCC)

A Retrieval-Augmented Generation agent that answers UCC regulatory
and filing procedure questions using ChromaDB for vector search and
Claude for answer generation with citations.

TODO: Implement the functions marked with TODO comments.
"""

import os
import sys

import anthropic
import chromadb

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
CHROMA_COLLECTION = "ucc_reference"
MODEL = "claude-sonnet-4-6"
TOP_K = 5


# ---------------------------------------------------------------------------
# Step 3: Index documents into ChromaDB
# ---------------------------------------------------------------------------
def index_documents(chunks: list[dict], collection) -> int:
    """
    Add all chunks to the ChromaDB collection.

    Args:
        chunks: List of chunk dicts with "text", "source", "chunk_index".
        collection: A ChromaDB collection object.

    Returns:
        The number of chunks indexed.
    """
    # TODO: Build three parallel lists: ids, documents, metadatas

    # TODO: Call collection.add(ids=..., documents=..., metadatas=...)

    # TODO: Return the count of indexed chunks
    pass


# ---------------------------------------------------------------------------
# Step 4: Query the RAG pipeline
# ---------------------------------------------------------------------------
def retrieve(query: str, collection, top_k: int = TOP_K) -> list[dict]:
    """
    Retrieve the top-k most relevant chunks for a query.

    Returns:
        A list of dicts with "text", "source", and "chunk_index".
    """
    # TODO: Call collection.query(query_texts=[query], n_results=top_k)

    # TODO: Parse and return results
    pass


def build_context(results: list[dict]) -> str:
    """
    Format retrieved chunks into a context string for the LLM prompt.
    """
    # TODO: Format each result with source metadata for citation
    pass


def ask(
    question: str,
    context: str,
    client: anthropic.Anthropic,
    conversation_history: list[dict],
) -> str:
    """
    Send the question + context to Claude and return the answer.
    """
    # TODO: Build system prompt for UCC regulatory Q&A

    # TODO: Construct user message with context + question

    # TODO: Call client.messages.create()

    # TODO: Return response text
    pass


# ---------------------------------------------------------------------------
# Step 6: Conversational loop
# ---------------------------------------------------------------------------
def main():
    """Run the interactive RAG agent."""
    # TODO: Import loader and chunker
    # TODO: Load documents from docs/
    # TODO: Chunk all documents
    # TODO: Initialize ChromaDB and index chunks
    # TODO: Initialize Anthropic client
    # TODO: Run conversation loop with special commands
    pass


if __name__ == "__main__":
    main()
