"""
Tests for Capstone 2, Domain C (UCC) — Loader and Chunker

Run from the domain-c-ucc directory:
    pytest tests/test_rag.py -v

These tests exercise the local pipeline components (loader and chunker)
and do NOT require an API key or any external services.
"""

import os
import sys
import tempfile
import shutil

import pytest

# ---------------------------------------------------------------------------
# Path setup — allow imports from the solution/ directory so tests work
# regardless of the current working directory.
# ---------------------------------------------------------------------------
DOMAIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOLUTION_DIR = os.path.join(DOMAIN_DIR, "solution")
DOCS_DIR = os.path.join(DOMAIN_DIR, "docs")

sys.path.insert(0, SOLUTION_DIR)

from loader import load_documents  # noqa: E402
from chunker import chunk_document, chunk_all  # noqa: E402


# ===========================================================================
# Loader tests
# ===========================================================================

class TestLoadDocuments:
    """Tests for loader.load_documents()."""

    def test_loads_all_five_docs(self):
        """load_documents() should find all 5 UCC reference documents in docs/."""
        docs = load_documents(DOCS_DIR)
        assert len(docs) == 5, (
            f"Expected 5 documents, got {len(docs)}. "
            f"Files found: {[d['filename'] for d in docs]}"
        )

    def test_returns_list_of_dicts_with_correct_keys(self):
        """Every document dict must have 'filename' and 'content' keys."""
        docs = load_documents(DOCS_DIR)
        for doc in docs:
            assert "filename" in doc, "Document dict missing 'filename' key"
            assert "content" in doc, "Document dict missing 'content' key"

    def test_filenames_are_expected(self):
        """The loaded filenames should match the known UCC docs."""
        expected_files = sorted([
            "collateral_classification.md",
            "filing_procedures_faq.md",
            "state_filing_handbook.md",
            "ucc_article9_guide.md",
            "ucc_data_dictionary.md",
        ])
        docs = load_documents(DOCS_DIR)
        actual_files = sorted(d["filename"] for d in docs)
        assert actual_files == expected_files

    def test_content_is_nonempty(self):
        """Every loaded document should have non-empty content."""
        docs = load_documents(DOCS_DIR)
        for doc in docs:
            assert len(doc["content"].strip()) > 0, (
                f"Document '{doc['filename']}' has empty content"
            )

    def test_raises_on_missing_directory(self):
        """load_documents() should raise FileNotFoundError for a bad path."""
        with pytest.raises(FileNotFoundError):
            load_documents("/nonexistent/path/that/does/not/exist")

    def test_skips_non_markdown_files(self):
        """load_documents() should ignore files that are not .md."""
        tmp_dir = tempfile.mkdtemp()
        try:
            with open(os.path.join(tmp_dir, "good.md"), "w") as f:
                f.write("Some content")
            with open(os.path.join(tmp_dir, "ignored.txt"), "w") as f:
                f.write("Should not be loaded")

            docs = load_documents(tmp_dir)
            assert len(docs) == 1
            assert docs[0]["filename"] == "good.md"
        finally:
            shutil.rmtree(tmp_dir)

    def test_empty_directory_returns_empty_list(self):
        """load_documents() on a directory with no .md files returns []."""
        tmp_dir = tempfile.mkdtemp()
        try:
            docs = load_documents(tmp_dir)
            assert docs == []
        finally:
            shutil.rmtree(tmp_dir)


# ===========================================================================
# Chunker tests
# ===========================================================================

class TestChunkDocument:
    """Tests for chunker.chunk_document()."""

    def test_produces_chunks_for_real_doc(self):
        """Chunking a real UCC doc should produce at least 1 chunk."""
        docs = load_documents(DOCS_DIR)
        chunks = chunk_document(docs[0])
        assert len(chunks) > 0, "Expected at least one chunk from a real document"

    def test_chunk_count_is_correct(self):
        """Verify the expected number of chunks for a known content length.

        With chunk_size=100 and overlap=20 the step is 80.
        For a 250-char string the chunks start at 0, 80, 160, 240 = 4 chunks.
        """
        doc = {"filename": "test.md", "content": "A" * 250}
        chunks = chunk_document(doc, chunk_size=100, overlap=20)
        assert len(chunks) == 4, f"Expected 4 chunks, got {len(chunks)}"

    def test_chunks_have_correct_metadata(self):
        """Each chunk must carry 'source' and 'chunk_index' metadata."""
        doc = {"filename": "ucc_article9_guide.md", "content": "X" * 500}
        chunks = chunk_document(doc, chunk_size=200, overlap=50)
        for i, chunk in enumerate(chunks):
            assert chunk["source"] == "ucc_article9_guide.md", (
                f"Chunk {i} has wrong source: {chunk['source']}"
            )
            assert chunk["chunk_index"] == i, (
                f"Chunk {i} has wrong chunk_index: {chunk['chunk_index']}"
            )
            assert "text" in chunk, f"Chunk {i} is missing 'text' key"

    def test_empty_document_produces_no_chunks(self):
        """An empty document should yield an empty chunk list."""
        doc = {"filename": "empty.md", "content": ""}
        chunks = chunk_document(doc)
        assert chunks == [], f"Expected no chunks for empty doc, got {len(chunks)}"

    def test_whitespace_only_document_produces_no_chunks(self):
        """A whitespace-only document should yield no chunks."""
        doc = {"filename": "blank.md", "content": "   \n\n\t  "}
        chunks = chunk_document(doc)
        assert chunks == [], f"Expected no chunks for whitespace doc, got {len(chunks)}"

    def test_overlap_works(self):
        """The last `overlap` chars of chunk i should equal the first `overlap`
        chars of chunk i+1 (when content is long enough)."""
        content = "ABCDEFGHIJKLMNOPQRSTUVWXYZ" * 20  # 520 chars
        doc = {"filename": "overlap_test.md", "content": content}
        overlap = 50
        chunks = chunk_document(doc, chunk_size=200, overlap=overlap)

        assert len(chunks) >= 2, "Need at least 2 chunks to test overlap"
        for i in range(len(chunks) - 1):
            tail_of_current = chunks[i]["text"][-overlap:]
            head_of_next = chunks[i + 1]["text"][:overlap]
            assert tail_of_current == head_of_next, (
                f"Overlap mismatch between chunk {i} and {i+1}:\n"
                f"  tail: {tail_of_current!r}\n"
                f"  head: {head_of_next!r}"
            )

    def test_small_document_single_chunk(self):
        """A document smaller than chunk_size should produce exactly 1 chunk."""
        doc = {"filename": "tiny.md", "content": "Short content"}
        chunks = chunk_document(doc, chunk_size=1000, overlap=200)
        assert len(chunks) == 1
        assert chunks[0]["text"] == "Short content"
        assert chunks[0]["chunk_index"] == 0

    def test_chunk_text_covers_full_content(self):
        """Every character in the original content should appear in at least
        one chunk (no gaps)."""
        content = "A" * 500
        doc = {"filename": "coverage.md", "content": content}
        chunks = chunk_document(doc, chunk_size=200, overlap=50)

        covered = set()
        step = max(200 - 50, 1)
        for i, chunk in enumerate(chunks):
            start = i * step
            for j in range(len(chunk["text"])):
                covered.add(start + j)

        for idx in range(len(content)):
            assert idx in covered, f"Character at index {idx} not covered by any chunk"


class TestChunkAll:
    """Tests for chunker.chunk_all()."""

    def test_chunk_all_returns_flat_list(self):
        """chunk_all() should return a flat list of chunks from all docs."""
        docs = load_documents(DOCS_DIR)
        all_chunks = chunk_all(docs, chunk_size=1000, overlap=200)
        assert isinstance(all_chunks, list)
        assert len(all_chunks) > 0

    def test_chunk_all_covers_all_documents(self):
        """Chunks from every loaded document should be present."""
        docs = load_documents(DOCS_DIR)
        all_chunks = chunk_all(docs, chunk_size=1000, overlap=200)
        sources_in_chunks = set(c["source"] for c in all_chunks)
        sources_in_docs = set(d["filename"] for d in docs)
        assert sources_in_chunks == sources_in_docs, (
            f"Chunk sources {sources_in_chunks} do not match "
            f"doc filenames {sources_in_docs}"
        )
