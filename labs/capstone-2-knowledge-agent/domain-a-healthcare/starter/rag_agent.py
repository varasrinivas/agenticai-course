"""
RAG Agent — Capstone 2, Domain A (Healthcare)

A Retrieval-Augmented Generation agent that answers clinical policy
questions using ChromaDB for vector search and Claude for answer
generation with citations.

TODO: Implement the functions marked with TODO comments.
"""

import os
import sys

import anthropic
import chromadb

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
CHROMA_COLLECTION = "healthcare_policies"
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
    # TODO: Build three parallel lists:
    #   ids       — unique ID per chunk, e.g. f"{chunk['source']}_{chunk['chunk_index']}"
    #   documents — the chunk text
    #   metadatas — dict with "source" and "chunk_index"

    # TODO: Call collection.add(ids=..., documents=..., metadatas=...)

    # TODO: Return the count of indexed chunks
    pass


# ---------------------------------------------------------------------------
# Step 4: Query the RAG pipeline
# ---------------------------------------------------------------------------
def retrieve(query: str, collection, top_k: int = TOP_K) -> list[dict]:
    """
    Retrieve the top-k most relevant chunks for a query.

    Args:
        query: The user's question.
        collection: ChromaDB collection.
        top_k: Number of results to return.

    Returns:
        A list of dicts with "text", "source", and "chunk_index".
    """
    # TODO: Call collection.query(query_texts=[query], n_results=top_k)

    # TODO: Parse the results into a list of dicts

    # TODO: Return the parsed results
    pass


def build_context(results: list[dict]) -> str:
    """
    Format retrieved chunks into a context string for the LLM prompt.
    Include source metadata so the model can cite them.

    Args:
        results: List of retrieved chunk dicts.

    Returns:
        A formatted context string.
    """
    # TODO: For each result, format as:
    #   [Source: {source}, Chunk {chunk_index}]
    #   {text}
    #
    # Join all formatted chunks with blank lines between them.
    pass


def ask(
    question: str,
    context: str,
    client: anthropic.Anthropic,
    conversation_history: list[dict],
) -> str:
    """
    Send the question + context to Claude and return the answer.

    Args:
        question: The user's question.
        context: The formatted context string from build_context().
        client: Anthropic client instance.
        conversation_history: List of prior messages for multi-turn context.

    Returns:
        The assistant's answer as a string.
    """
    # TODO: Build a system prompt that instructs Claude to:
    #   - Answer based ONLY on the provided context
    #   - Cite sources using [Source: filename, Chunk N]
    #   - Say "I don't have enough information" if the context doesn't cover the question

    # TODO: Construct the user message with context + question

    # TODO: Call client.messages.create() with model, system, and messages

    # TODO: Return the response text
    pass


# ---------------------------------------------------------------------------
# Step 6: Conversational loop
# ---------------------------------------------------------------------------
def main():
    """Run the interactive RAG agent."""
    # TODO: Import loader and chunker
    # from loader import load_documents
    # from chunker import chunk_all

    # TODO: Load documents from docs/

    # TODO: Chunk all documents

    # TODO: Initialize ChromaDB client (in-memory or persistent)

    # TODO: Create or get collection

    # TODO: Index chunks (skip if collection already populated)

    # TODO: Initialize Anthropic client

    # TODO: Print welcome message

    # TODO: Run conversation loop:
    #   - Read user input
    #   - Handle special commands: "quit", "sources"
    #   - Retrieve relevant chunks
    #   - Build context
    #   - Call ask()
    #   - Print the response
    #   - Append to conversation history
    pass


if __name__ == "__main__":
    main()
