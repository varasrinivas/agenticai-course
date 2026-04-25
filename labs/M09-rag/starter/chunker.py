"""
M09 Lab — Step 1: Document Loader & Chunker
============================================
Load markdown documents and split them into chunks for RAG.

Two chunking strategies:
  1. Fixed-size with overlap (character-based)
  2. Header-based semantic chunking (split on ## headings)

Run:
    python starter/chunker.py
"""

import os
import glob


# ---------------------------------------------------------------------------
# Document Loading (COMPLETE — no changes needed)
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
# TODO 1: Fixed-Size Chunking
# ---------------------------------------------------------------------------

def chunk_document(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """
    Split `text` into chunks of approximately `chunk_size` characters
    with `overlap` characters of overlap between consecutive chunks.

    Rules:
      - Each chunk should be at most `chunk_size` characters.
      - Consecutive chunks overlap by `overlap` characters.
      - The last chunk may be smaller than `chunk_size`.
      - If the text is shorter than `chunk_size`, return it as a single chunk.

    Example (chunk_size=10, overlap=3):
      text = "abcdefghijklmnopqrst"  (20 chars)
      chunks = ["abcdefghij", "hijklmnopq", "opqrst"]

    Returns:
      A list of chunk strings.
    """
    # TODO: Implement fixed-size chunking with overlap.
    # Hint: use a while loop with a `start` pointer.
    #   - Each iteration, take text[start : start + chunk_size]
    #   - Advance start by (chunk_size - overlap)
    #   - Stop when start >= len(text)
    pass


# ---------------------------------------------------------------------------
# TODO 2: Header-Based Semantic Chunking
# ---------------------------------------------------------------------------

def chunk_by_headers(text: str, filename: str = "unknown") -> list[dict]:
    """
    Split text on markdown ## headers to create semantic chunks.

    Each chunk should contain the text under one ## heading (including the
    heading line itself). Text that appears before the first ## heading
    should be captured as an "Introduction" chunk.

    Returns a list of dicts:
      [
        {
          "text": "## Heading\n\nParagraph text...",
          "metadata": {
            "source": filename,
            "header": "Heading",          # the heading text (without ##)
            "chunk_index": 0
          }
        },
        ...
      ]

    Hints:
      - Split the text on lines that start with "## " (two hashes + space).
      - Keep the heading line as part of the chunk.
      - Strip leading/trailing whitespace from each chunk.
      - Skip empty chunks.
    """
    # TODO: Implement header-based semantic chunking.
    # Step 1: Split the text into lines.
    # Step 2: Walk through lines, starting a new chunk each time you see "## ".
    # Step 3: Collect text before the first heading as "Introduction".
    # Step 4: Build the list of chunk dicts with metadata.
    pass


# ---------------------------------------------------------------------------
# TODO 3: Add Metadata to Fixed-Size Chunks
# ---------------------------------------------------------------------------

def chunk_with_metadata(
    text: str,
    filename: str = "unknown",
    chunk_size: int = 500,
    overlap: int = 50,
) -> list[dict]:
    """
    Combine fixed-size chunking with metadata.

    Uses `chunk_document()` to split the text, then wraps each chunk in a
    dict with metadata.

    Returns:
      [
        {
          "text": "chunk text...",
          "metadata": {
            "source": filename,
            "chunk_index": 0,
            "chunk_method": "fixed_size",
            "chunk_size": 500,
            "overlap": 50
          }
        },
        ...
      ]
    """
    # TODO: Call chunk_document() and wrap each result with metadata.
    pass


# ---------------------------------------------------------------------------
# Main — Test Your Implementation
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
        if chunks:
            all_fixed_chunks.extend(chunks)
            print(f"  {doc['filename']}: {len(chunks)} chunks")

    if all_fixed_chunks:
        avg_size = sum(len(c) for c in all_fixed_chunks) / len(all_fixed_chunks)
        print(f"\n  Total fixed-size chunks : {len(all_fixed_chunks)}")
        print(f"  Average chunk size      : {avg_size:.0f} chars")
        print(f"  Smallest chunk          : {min(len(c) for c in all_fixed_chunks)} chars")
        print(f"  Largest chunk           : {max(len(c) for c in all_fixed_chunks)} chars")
    else:
        print("\n  *** chunk_document() returned None — implement TODO 1 ***")

    # --- Header-based chunking ---
    print("\n" + "=" * 60)
    print("STEP 3: Header-Based Semantic Chunking")
    print("=" * 60)
    all_header_chunks = []
    for doc in documents:
        chunks = chunk_by_headers(doc["content"], filename=doc["filename"])
        if chunks:
            all_header_chunks.extend(chunks)
            print(f"  {doc['filename']}: {len(chunks)} chunks")
            for chunk in chunks:
                header = chunk["metadata"]["header"]
                size = len(chunk["text"])
                print(f"    - '{header}' ({size} chars)")

    if all_header_chunks:
        avg_size = sum(len(c["text"]) for c in all_header_chunks) / len(all_header_chunks)
        print(f"\n  Total header chunks : {len(all_header_chunks)}")
        print(f"  Average chunk size  : {avg_size:.0f} chars")
    else:
        print("\n  *** chunk_by_headers() returned None — implement TODO 2 ***")

    # --- Comparison ---
    print("\n" + "=" * 60)
    print("COMPARISON")
    print("=" * 60)
    if all_fixed_chunks and all_header_chunks:
        print(f"  Fixed-size chunks : {len(all_fixed_chunks)}")
        print(f"  Header chunks     : {len(all_header_chunks)}")
        print(f"  Header chunking produces fewer, more meaningful chunks.")
    else:
        print("  Complete TODOs 1 and 2 to see the comparison.")


if __name__ == "__main__":
    main()
