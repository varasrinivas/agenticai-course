"""
Document Loader — Capstone 2, Domain C (UCC) — SOLUTION

Reads all Markdown files from the docs/ directory and returns them
as a list of dictionaries with filename and content.
"""

import os
import sys


def load_documents(docs_dir: str) -> list[dict]:
    """
    Load all .md files from the given directory.

    Args:
        docs_dir: Path to the directory containing Markdown documents.

    Returns:
        A list of dicts, each with keys:
            - "filename": the file name
            - "content": the full text content of the file

    Raises:
        FileNotFoundError: If docs_dir does not exist.
    """
    if not os.path.isdir(docs_dir):
        raise FileNotFoundError(f"Documents directory not found: {docs_dir}")

    documents: list[dict] = []

    for fname in sorted(os.listdir(docs_dir)):
        if not fname.endswith(".md"):
            continue

        filepath = os.path.join(docs_dir, fname)

        try:
            with open(filepath, "r", encoding="utf-8") as fh:
                content = fh.read()
        except (OSError, UnicodeDecodeError) as exc:
            print(f"Warning: Could not read {fname}: {exc}", file=sys.stderr)
            continue

        if not content.strip():
            print(f"Warning: Skipping empty file {fname}", file=sys.stderr)
            continue

        documents.append({"filename": fname, "content": content})

    return documents


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    docs_path = os.path.join(script_dir, "..", "docs")

    try:
        documents = load_documents(docs_path)
        if not documents:
            print("No documents found.")
            sys.exit(1)

        print(f"Loaded {len(documents)} documents:\n")
        for doc in documents:
            print(f"  {doc['filename']:40s}  {len(doc['content']):>6,} chars")
    except FileNotFoundError as exc:
        print(f"Error: {exc}")
        sys.exit(1)
