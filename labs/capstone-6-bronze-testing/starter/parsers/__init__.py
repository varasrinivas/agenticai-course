"""
UCC Filing Source File Parsers

Each parser reads a specific file format and returns a list of dictionaries
with normalized field names matching the Bronze canonical schema.
"""

from .xml_parser import parse_xml
from .pipe_csv_parser import parse_pipe_csv
from .comma_csv_parser import parse_comma_csv
from .fixed_width_parser import parse_fixed_width
from .json_parser import parse_json

PARSER_REGISTRY = {
    "xml": parse_xml,
    "pipe_csv": parse_pipe_csv,
    "comma_csv": parse_comma_csv,
    "fixed_width": parse_fixed_width,
    "json": parse_json,
}


def get_parser(format_type: str):
    """Return the appropriate parser function for the given format type."""
    parser = PARSER_REGISTRY.get(format_type)
    if parser is None:
        raise ValueError(f"Unknown format type: {format_type}. Available: {list(PARSER_REGISTRY.keys())}")
    return parser
