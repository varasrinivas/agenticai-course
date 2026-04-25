"""
M09 Lab — Step 1: Document Loader & Chunker (SOLUTION)
=======================================================
Load markdown documents and split them into chunks for RAG.

Run:
    python solution/chunker.py
"""

import os
import glob


# ---------------------------------------------------------------------------
# Document Loading
# ---------------------------------------------------------------------------

def load_documents(docs_dir: str) -> list[dict]:
    """
    Load all .md files from the docs directory.
    Returns a list of dicts: [{"filename": "...", "content": "..."}, ...]
    """
    documents = []
    md_files = sorted(glob.glob(os.path.join(docs_dir, "*.md")))

    if not md_files:
        raise FileNotFoundError(f"No .md files found in {docs_dir}")

    for filepath in md_files:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        documents.append({
            "filename": os.path.basename(filepath),
            "content": content,
        })
        print(f"  Loaded: {os.path.basename(filepath)} ({len(content)} chars)")

    return documents


# ---------------------------------------------------------------------------
# Fixed-Size Chunking
# ---------------------------------------------------------------------------

def chunk_document(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """
    Split text into chunks of approximately chunk_size characters
    with overlap characters of overlap between consecutive chunks.
    """
    if not text:
        return []

    chunks = []
    start = 0
    step = chunk_size - overlap

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += step

    return chunks


# ---------------------------------------------------------------------------
# Header-Based Semantic Chunking
# ---------------------------------------------------------------------------

def chunk_by_headers(text: str, filename: str = "unknown") -> list[dict]:
    """
    Split text on markdown ## headers to create semantic chunks.
    """
    lines = text.split("\n")
    chunks = []
    current_lines = []
    current_header = "Introduction"
    chunk_index = 0

    for line in lines:
        if line.startswith("## "):
            # Save previous chunk
            if current_lines:
                chunk_text = "\n".join(current_lines).strip()
                if chunk_text:
                    chunks.append({
                        "text": chunk_text,
                        "metadata": {
                            "source": filename,
                            "header": current_header,
                            "chunk_index": chunk_index,
                        },
                    })
                    chunk_index += 1

            current_header = line.lstrip("# ").strip()
            current_lines = [line]
        else:
            current_lines.append(line)

    # Save the last chunk
    if current_lines:
        chunk_text = "\n".join(current_lines).strip()
        if chunk_text:
            chunks.append({
                "text": chunk_text,
                "metadata": {
                    "source": filename,
                    "header": current_header,
                    "chunk_index": chunk_index,
                },
            })

    return chunks


# ---------------------------------------------------------------------------
# Fixed-Size Chunks with Metadata
# ---------------------------------------------------------------------------

def chunk_with_metadata(
    text: str,
    filename: str = "unknown",
    chunk_size: int = 500,
    overlap: int = 50,
) -> list[dict]:
    """Combine fixed-size chunking with metadata."""
    raw_chunks = chunk_document(text, chunk_size, overlap)
    return [
        {
            "text": chunk,
            "metadata": {
                "source": filename,
                "chunk_index": i,
                "chunk_method": "fixed_size",
                "chunk_size": chunk_size,
                "overlap": overlap,
            },
        }
        for i, chunk in enumerate(raw_chunks)
    ]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    docs_dir = os.path.join(os.path.dirname(__file__), "..", "docs")

    print("=" * 60)
    print("STEP 1: Loading Documents")
    print("=" * 60)
    documents = load_documents(docs_dir)
    print(f"\nLoaded {len(documents)} documents.\n")

    # --- Fixed-size chunking ---
    print("=" * 60)
    print("STEP 2: Fixed-Size Chunking (chunk_size=500, overlap=50)")
    print("=" * 60)
    all_fixed_chunks = []
    for doc in documents:
        chunks = chunk_document(doc["content"], chunk_size=500, overlap=50)
        all_fixed_chunks.extend(chunks)
        print(f"  {doc['filename']}: {len(chunks)} chunks")

    avg_size = sum(len(c) for c in all_fixed_chunks) / len(all_fixed_chunks)
    print(f"\n  Total fixed-size chunks : {len(all_fixed_chunks)}")
    print(f"  Average chunk size      : {avg_size:.0f} chars")
    print(f"  Smallest chunk          : {min(len(c) for c in all_fixed_chunks)} chars")
    print(f"  Largest chunk           : {max(len(c) for c in all_fixed_chunks)} chars")

    # --- Header-based chunking ---
    print("\n" + "=" * 60)
    print("STEP 3: Header-Based Semantic Chunking")
    print("=" * 60)
    all_header_chunks = []
    for doc in documents:
        chunks = chunk_by_headers(doc["content"], filename=doc["filename"])
        all_header_chunks.extend(chunks)
        print(f"  {doc['filename']}: {len(chunks)} chunks")
        for chunk in chunks:
            header = chunk["metadata"]["header"]
            size = len(chunk["text"])
            print(f"    - '{header}' ({size} chars)")

    avg_size = sum(len(c["text"]) for c in all_header_chunks) / len(all_header_chunks)
    print(f"\n  Total header chunks : {len(all_header_chunks)}")
    print(f"  Average chunk size  : {avg_size:.0f} chars")

    # --- Comparison ---
    print("\n" + "=" * 60)
    print("COMPARISON")
    print("=" * 60)
    print(f"  Fixed-size chunks : {len(all_fixed_chunks)}")
    print(f"  Header chunks     : {len(all_header_chunks)}")
    print(f"  Header chunking produces fewer, more meaningful chunks.")


if __name__ == "__main__":
    main()
