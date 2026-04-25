"""
RAG Agent — Capstone 2, Domain A (Healthcare) — SOLUTION

A Retrieval-Augmented Generation agent that answers clinical policy
questions using ChromaDB for vector search and Claude for answer
generation with citations.
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
CHROMA_COLLECTION = "healthcare_policies"
MODEL = "claude-sonnet-4-20250514"
TOP_K = 5

SYSTEM_PROMPT = """\
You are a clinical policy reference assistant. Your job is to answer questions
about healthcare payer clinical policies using ONLY the provided context.

Rules:
1. Base your answer strictly on the provided context passages. Do not use
   outside knowledge.
2. Cite every factual claim using the format [Source: <filename>, Chunk <N>].
3. If the context does not contain enough information to answer the question,
   say: "I don't have enough information in the loaded policies to answer
   that question."
4. When listing criteria, quote them accurately from the source documents.
5. Use clear, professional language appropriate for healthcare administrators
   and clinical staff.
"""


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

    # ChromaDB supports batching; add all at once for small corpora
    collection.add(ids=ids, documents=documents, metadatas=metadatas)
    return len(ids)


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
    """
    Format retrieved chunks into a context string for the LLM prompt.
    Include source metadata so the model can cite them.

    Args:
        results: List of retrieved chunk dicts.

    Returns:
        A formatted context string.
    """
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
    user_message = (
        f"Context (retrieved from policy documents):\n\n{context}\n\n"
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
    # Resolve paths
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
    chroma_client = chromadb.Client()  # in-memory
    collection = chroma_client.get_or_create_collection(name=CHROMA_COLLECTION)

    if collection.count() == 0:
        count = index_documents(chunks, collection)
        print(f"  Indexed {count} chunks.")
    else:
        print(f"  Collection already has {collection.count()} items.")

    # Step 4-5: Initialize Anthropic client
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable is not set.")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    # Step 6: Conversation loop
    conversation_history: list[dict] = []

    print("\n" + "=" * 60)
    print("Clinical Policy Q&A Agent")
    print("=" * 60)
    print("Ask questions about clinical policies.")
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
            print("\nLoaded policy documents:")
            for doc in documents:
                print(f"  - {doc['filename']}")
            print()
            continue

        # Retrieve relevant chunks
        results = retrieve(user_input, collection, top_k=TOP_K)
        context = build_context(results)

        # Ask Claude
        answer = ask(user_input, context, client, conversation_history)

        # Update conversation history
        conversation_history.append({"role": "user", "content": user_input})
        conversation_history.append({"role": "assistant", "content": answer})

        # Keep history manageable (last 10 turns)
        if len(conversation_history) > 20:
            conversation_history = conversation_history[-20:]

        print(f"\nAgent: {answer}\n")


if __name__ == "__main__":
    main()
