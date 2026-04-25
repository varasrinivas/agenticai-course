"""
Document Chunker — Capstone 2, Domain B (Ecommerce) — SOLUTION

Splits loaded documents into overlapping chunks suitable for
embedding and vector search.
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
    content = document["content"]
    source = document["filename"]

    if not content.strip():
        return []

    chunks: list[dict] = []
    start = 0
    chunk_index = 0
    step = max(chunk_size - overlap, 1)

    while start < len(content):
        end = start + chunk_size
        text = content[start:end]

        if text.strip():
            chunks.append(
                {
                    "text": text,
                    "source": source,
                    "chunk_index": chunk_index,
                }
            )
            chunk_index += 1

        start += step

    return chunks


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
    all_chunks: list[dict] = []
    for doc in documents:
        all_chunks.extend(chunk_document(doc, chunk_size, overlap))
    return all_chunks


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
