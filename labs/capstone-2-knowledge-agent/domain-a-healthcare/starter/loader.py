"""
Document Loader — Capstone 2, Domain A (Healthcare)

Reads all Markdown files from the docs/ directory and returns them
as a list of dictionaries with filename and content.

TODO: Implement the load_documents() function.
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
            - "filename": the file name (e.g., "policy_mri_brain.md")
            - "content": the full text content of the file

    Raises:
        FileNotFoundError: If docs_dir does not exist.
    """
    # TODO: Check that docs_dir exists; raise FileNotFoundError if not

    # TODO: Iterate over files in docs_dir

    # TODO: Filter for .md files only

    # TODO: Read each file's content (UTF-8 encoding)

    # TODO: Skip empty files

    # TODO: Append {"filename": ..., "content": ...} to results list

    # TODO: Return the list
    pass


if __name__ == "__main__":
    # Resolve the docs/ directory relative to this script
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
