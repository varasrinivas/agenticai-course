"""
Document Chunker — Capstone 2, Domain B (Ecommerce)

Splits loaded documents into overlapping chunks suitable for
embedding and vector search.

TODO: Implement the chunk_document() and chunk_all() functions.
"""

import os
import sys


def chunk_document(
    document: dict,
    chunk_size: int = 1000,
    overlap: int = 200,
) -> list[dict]:
    """
    Split a single document into overlapping chunks.

    Args:
        document: A dict with "filename" and "content" keys.
        chunk_size: Target size of each chunk in characters.
        overlap: Number of characters to overlap between consecutive chunks.

    Returns:
        A list of chunk dicts, each with keys:
            - "text": the chunk text
            - "source": the source filename
            - "chunk_index": integer index of this chunk within the document
    """
    # TODO: Extract the content string from the document dict

    # TODO: Handle edge case where content is shorter than chunk_size

    # TODO: Slide a window across the content:
    #   - Start at position 0
    #   - Each chunk is content[start : start + chunk_size]
    #   - Advance start by (chunk_size - overlap) each iteration
    #   - Continue until start >= len(content)

    # TODO: Attach metadata: source filename and chunk_index

    # TODO: Return the list of chunks
    pass


def chunk_all(
    documents: list[dict],
    chunk_size: int = 1000,
    overlap: int = 200,
) -> list[dict]:
    """
    Chunk every document in the list.

    Returns:
        A flat list of all chunks across all documents.
    """
    # TODO: Iterate over documents, call chunk_document, collect results
    pass


if __name__ == "__main__":
    from loader import load_documents

    script_dir = os.path.dirname(os.path.abspath(__file__))
    docs_path = os.path.join(script_dir, "..", "docs")

    documents = load_documents(docs_path)
    if not documents:
        print("No documents loaded.")
        sys.exit(1)

    all_chunks = chunk_all(documents, chunk_size=1000, overlap=200)
    print(f"Total chunks: {len(all_chunks)}\n")

    for doc in documents:
        doc_chunks = [c for c in all_chunks if c["source"] == doc["filename"]]
        print(f"  {doc['filename']:40s}  {len(doc_chunks):>3} chunks")

    print(f"\nFirst chunk of '{documents[0]['filename']}':")
    print("-" * 60)
    print(all_chunks[0]["text"][:300] + "...")
