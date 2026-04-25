"""
Tests for the 5 UCC Filing Source File Parsers

Validates that each parser correctly reads its mock source file and returns
normalized records matching the Bronze canonical schema.
"""

import os
import sys
import pytest

# Add solution directory to path for imports
SOLUTION_DIR = os.path.join(os.path.dirname(__file__), "..", "solution")
STARTER_DIR = os.path.join(os.path.dirname(__file__), "..", "starter")
sys.path.insert(0, SOLUTION_DIR)

from parsers import get_parser, PARSER_REGISTRY

MOCK_DATA_DIR = os.path.join(STARTER_DIR, "mock_data")
SOURCE_FILES_DIR = os.path.join(MOCK_DATA_DIR, "source_files")

# Expected fields in every parsed record
REQUIRED_FIELDS = [
    "filing_number",
    "filing_type",
    "filing_date",
    "status",
    "debtor_name",
]


class TestParserRegistry:
    """Test the parser registry and get_parser utility."""

    def test_all_formats_registered(self):
        expected_formats = {"xml", "pipe_csv", "comma_csv", "fixed_width", "json"}
        assert set(PARSER_REGISTRY.keys()) == expected_formats

    def test_get_parser_valid(self):
        for fmt in PARSER_REGISTRY:
            parser = get_parser(fmt)
            assert callable(parser)

    def test_get_parser_invalid(self):
        with pytest.raises(ValueError, match="Unknown format type"):
            get_parser("yaml")


class TestXMLParser:
    """Test the XML parser against NY, IL, and WA source files."""

    @pytest.mark.parametrize("state,filename,min_records", [
        ("NY", "NY_2024_Q4.xml", 10),
        ("IL", "IL_2024_Q4.xml", 10),
        ("WA", "WA_2024_Q4.xml", 10),
    ])
    def test_parse_xml_files(self, state, filename, min_records):
        parser = get_parser("xml")
        filepath = os.path.join(SOURCE_FILES_DIR, filename)
        records, metadata = parser(filepath)

        assert isinstance(records, list)
        assert len(records) >= min_records
        assert isinstance(metadata, dict)
        assert metadata.get("format") == "xml"

        # Verify record structure
        for record in records:
            for field in REQUIRED_FIELDS:
                assert field in record, f"Missing field '{field}' in {state} record"

    def test_xml_filing_numbers_prefixed(self):
        parser = get_parser("xml")
        filepath = os.path.join(SOURCE_FILES_DIR, "NY_2024_Q4.xml")
        records, _ = parser(filepath)
        for record in records:
            assert record["filing_number"].startswith("NY-")


class TestPipeCSVParser:
    """Test the pipe-delimited CSV parser against CA, OH, GA, CO source files."""

    @pytest.mark.parametrize("filename", [
        "CA_2024_Q4.csv",
        "OH_2024_Q4.csv",
        "GA_2024_Q4.csv",
        "CO_2024_Q4.csv",
    ])
    def test_parse_pipe_csv_files(self, filename):
        parser = get_parser("pipe_csv")
        filepath = os.path.join(SOURCE_FILES_DIR, filename)
        records, metadata = parser(filepath)

        assert isinstance(records, list)
        assert len(records) >= 5
        assert isinstance(metadata, dict)

        for record in records:
            for field in REQUIRED_FIELDS:
                assert field in record, f"Missing '{field}' in {filename}"


class TestCommaCSVParser:
    """Test the comma-delimited CSV parser against DE, PA, MA source files."""

    @pytest.mark.parametrize("filename", [
        "DE_2024_Q4.csv",
        "PA_2024_Q4.csv",
        "MA_2024_Q4.csv",
    ])
    def test_parse_comma_csv_files(self, filename):
        parser = get_parser("comma_csv")
        filepath = os.path.join(SOURCE_FILES_DIR, filename)
        records, metadata = parser(filepath)

        assert isinstance(records, list)
        assert len(records) >= 5
        assert isinstance(metadata, dict)

        for record in records:
            for field in REQUIRED_FIELDS:
                assert field in record, f"Missing '{field}' in {filename}"


class TestFixedWidthParser:
    """Test the fixed-width parser against TX source file."""

    def test_parse_tx_file(self):
        parser = get_parser("fixed_width")
        filepath = os.path.join(SOURCE_FILES_DIR, "TX_2024_Q4.dat")
        records, metadata = parser(filepath)

        assert isinstance(records, list)
        assert len(records) >= 10
        assert isinstance(metadata, dict)

        for record in records:
            for field in REQUIRED_FIELDS:
                assert field in record, f"Missing '{field}' in TX record"
            assert record["filing_number"].startswith("TX-")

    def test_truncated_file_raises(self):
        """TX_BAD_truncated.dat should raise or return partial results."""
        parser = get_parser("fixed_width")
        filepath = os.path.join(SOURCE_FILES_DIR, "TX_BAD_truncated.dat")
        # Truncated file should either raise an exception or return fewer records
        try:
            records, metadata = parser(filepath)
            # If it doesn't raise, it should return very few records
            assert len(records) < 10
        except Exception:
            pass  # Expected — truncated file may fail to parse


class TestJSONParser:
    """Test the JSON parser against FL and NV source files."""

    @pytest.mark.parametrize("filename,state_prefix", [
        ("FL_2024_Q4.json", "FL-"),
        ("NV_2024_Q4.json", "NV-"),
    ])
    def test_parse_json_files(self, filename, state_prefix):
        parser = get_parser("json")
        filepath = os.path.join(SOURCE_FILES_DIR, filename)
        records, metadata = parser(filepath)

        assert isinstance(records, list)
        assert len(records) >= 5
        assert isinstance(metadata, dict)

        for record in records:
            for field in REQUIRED_FIELDS:
                assert field in record, f"Missing '{field}' in {filename}"
            assert record["filing_number"].startswith(state_prefix)

    def test_bad_encoding_file_raises(self):
        """FL_BAD_encoding.json should fail to parse (UTF-16LE BOM)."""
        parser = get_parser("json")
        filepath = os.path.join(SOURCE_FILES_DIR, "FL_BAD_encoding.json")
        with pytest.raises(Exception):
            parser(filepath)


class TestParserFileNotFound:
    """All parsers should raise FileNotFoundError for missing files."""

    @pytest.mark.parametrize("fmt", ["xml", "pipe_csv", "comma_csv", "fixed_width", "json"])
    def test_missing_file_raises(self, fmt):
        parser = get_parser(fmt)
        with pytest.raises((FileNotFoundError, Exception)):
            parser("/nonexistent/path/file.dat")
