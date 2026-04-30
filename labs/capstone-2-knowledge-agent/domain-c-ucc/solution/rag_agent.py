"""
RAG Agent — Capstone 2, Domain C (UCC) — SOLUTION

A Retrieval-Augmented Generation agent that answers UCC regulatory
and filing procedure questions using ChromaDB for vector search and
Claude for answer generation with citations.
"""

import os
import sys

import anthropic
import chromadb

from loader import load_documents
from chunker import chunk_all

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
CHROMA_COLLECTION = "ucc_reference"
MODEL = "claude-sonnet-4-6"
TOP_K = 5

SYSTEM_PROMPT = """\
You are a UCC (Uniform Commercial Code) regulatory reference assistant.
Your job is to answer questions about UCC Article 9 secured transactions,
filing procedures, collateral classification, and related regulatory topics
using ONLY the provided context.

Rules:
1. Base your answer strictly on the provided context passages. Do not use
   outside knowledge.
2. Cite every factual claim using the format [Source: <filename>, Chunk <N>].
3. If the context does not contain enough information to answer the question,
   say: "I don't have enough information in the loaded reference documents
   to answer that question."
4. When citing legal rules or procedures, quote them accurately from the
   source documents.
5. Use clear, professional language appropriate for legal, compliance, and
   data engineering staff.
"""


# ---------------------------------------------------------------------------
# Step 3: Index documents into ChromaDB
# ---------------------------------------------------------------------------
def index_documents(chunks: list[dict], collection) -> int:
    """Add all chunks to the ChromaDB collection."""
    ids = []
    documents = []
    metadatas = []

    for chunk in chunks:
        chunk_id = f"{chunk['source']}_{chunk['chunk_index']}"
        ids.append(chunk_id)
        documents.append(chunk["text"])
        metadatas.append(
            {"source": chunk["source"], "chunk_index": chunk["chunk_index"]}
        )

    collection.add(ids=ids, documents=documents, metadatas=metadatas)
    return len(ids)


# ---------------------------------------------------------------------------
# Step 4: Query the RAG pipeline
# ---------------------------------------------------------------------------
def retrieve(query: str, collection, top_k: int = TOP_K) -> list[dict]:
    """Retrieve the top-k most relevant chunks for a query."""
    results = collection.query(query_texts=[query], n_results=top_k)

    parsed: list[dict] = []
    for i in range(len(results["ids"][0])):
        parsed.append(
            {
                "text": results["documents"][0][i],
                "source": results["metadatas"][0][i]["source"],
                "chunk_index": results["metadatas"][0][i]["chunk_index"],
            }
        )

    return parsed


def build_context(results: list[dict]) -> str:
    """Format retrieved chunks into a context string with source metadata."""
    blocks: list[str] = []
    for r in results:
        header = f"[Source: {r['source']}, Chunk {r['chunk_index']}]"
        blocks.append(f"{header}\n{r['text']}")
    return "\n\n---\n\n".join(blocks)


def ask(
    question: str,
    context: str,
    client: anthropic.Anthropic,
    conversation_history: list[dict],
) -> str:
    """Send the question + context to Claude and return the answer."""
    user_message = (
        f"Context (retrieved from UCC reference documents):\n\n{context}\n\n"
        f"---\n\nQuestion: {question}"
    )

    messages = conversation_history + [{"role": "user", "content": user_message}]

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            messages=messages,
        )
        return response.content[0].text
    except anthropic.APIError as exc:
        return f"API error: {exc}"


# ---------------------------------------------------------------------------
# Step 6: Conversational loop
# ---------------------------------------------------------------------------
def main():
    """Run the interactive RAG agent."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    docs_path = os.path.join(script_dir, "..", "docs")

    # Step 1: Load documents
    print("Loading documents...")
    documents = load_documents(docs_path)
    if not documents:
        print("No documents found. Check the docs/ directory.")
        sys.exit(1)
    print(f"  Loaded {len(documents)} documents.")

    # Step 2: Chunk documents
    print("Chunking documents...")
    chunks = chunk_all(documents, chunk_size=1000, overlap=200)
    print(f"  Created {len(chunks)} chunks.")

    # Step 3: Initialize ChromaDB and index
    print("Indexing into ChromaDB...")
    chroma_client = chromadb.Client()
    collection = chroma_client.get_or_create_collection(name=CHROMA_COLLECTION)

    if collection.count() == 0:
        count = index_documents(chunks, collection)
        print(f"  Indexed {count} chunks.")
    else:
        print(f"  Collection already has {collection.count()} items.")

    # Initialize Anthropic client
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable is not set.")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    # Conversation loop
    conversation_history: list[dict] = []

    print("\n" + "=" * 60)
    print("UCC Regulatory Reference Agent")
    print("=" * 60)
    print("Ask questions about UCC Article 9, filing procedures,")
    print("collateral classification, and secured transactions.")
    print("Commands: 'sources' = list documents, 'quit' = exit")
    print("=" * 60 + "\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue

        if user_input.lower() == "quit":
            print("Goodbye!")
            break

        if user_input.lower() == "sources":
            print("\nLoaded reference documents:")
            for doc in documents:
                print(f"  - {doc['filename']}")
            print()
            continue

        results = retrieve(user_input, collection, top_k=TOP_K)
        context = build_context(results)

        answer = ask(user_input, context, client, conversation_history)

        conversation_history.append({"role": "user", "content": user_input})
        conversation_history.append({"role": "assistant", "content": answer})

        if len(conversation_history) > 20:
            conversation_history = conversation_history[-20:]

        print(f"\nAgent: {answer}\n")


if __name__ == "__main__":
    main()
