"""
M19 Lab — Trace Viewer (Starter)
=================================
Render traces as a tree in the terminal and export to JSON.

KEY CONCEPT: A trace is a tree of spans. The viewer walks that tree
and draws it with box-drawing characters, color-codes each span by
type, and shows timing as a percentage of total duration. This is
the same idea behind Jaeger's UI, Langfuse's trace view, and
Chrome DevTools' flame charts.

Usage:
    python trace_viewer.py
"""

import json
import sys
import os
from typing import Optional

# Ensure Unicode output works on Windows terminals
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(__file__))
from trace_model import Trace, Span, SpanContext
from structured_logger import StructuredLogger
from instrumenter import MockUCCAgent, InstrumentedAgent


# =============================================================================
# ANSI COLOR HELPERS
# =============================================================================

# WHAT: ANSI escape codes to color terminal output by span type.
# WHY:  Color makes it immediately obvious which spans are LLM calls
#   (blue = expensive), tool calls (green = fast), or errors (red = fix me).
# GOTCHA: Some terminals don't support ANSI colors. The NO_COLOR env
#   var is the standard way to disable them.

class Colors:
    """ANSI color codes for terminal output."""
    BLUE = "\033[94m"       # LLM calls
    GREEN = "\033[92m"      # Tool executions
    RED = "\033[91m"        # Errors
    YELLOW = "\033[93m"     # Warnings
    CYAN = "\033[96m"       # Trace metadata
    GRAY = "\033[90m"       # Secondary info
    BOLD = "\033[1m"        # Emphasis
    RESET = "\033[0m"       # Reset to default

    @staticmethod
    def enabled() -> bool:
        """Check if colors should be used (respect NO_COLOR env var)."""
        return os.environ.get("NO_COLOR") is None

    @classmethod
    def colorize(cls, text: str, color: str) -> str:
        """Wrap text in color codes if colors are enabled."""
        if cls.enabled():
            return f"{color}{text}{cls.RESET}"
        return text


def get_span_color(span: Span) -> str:
    """Return the appropriate color for a span based on its name/status."""
    # TODO:
    # - If span.status == "error", return Colors.RED
    # - If span.name contains "llm", return Colors.BLUE
    # - If span.name contains "tool", return Colors.GREEN
    # - Otherwise return Colors.CYAN
    pass


# =============================================================================
# TRACE RENDERER
# =============================================================================

# WHAT: Walks the trace's span tree and draws each span as a line
#   with box-drawing characters showing parent-child relationships.
# WHY:  A flat list of spans is hard to read. The tree view shows
#   causality (which spans are children of which) and timing at a glance.
# GOTCHA: The tree-drawing logic uses "is this the last child?" to
#   decide between the junction characters.

def render_trace(trace: Trace) -> str:
    """
    Render a trace as a colored tree in the terminal.

    Returns the rendered string (also prints it).
    """
    # TODO: Implement trace rendering:
    #
    # 1. Build the header:
    #    - "Trace {trace_id}  |  Total: {duration}ms  |  {N} spans"
    #    - A separator line of dashes
    #    Color the header with Colors.CYAN + Colors.BOLD
    #
    # 2. Render the root span:
    #    - Format: "[{duration}ms] {name}"
    #    - Color based on get_span_color()
    #
    # 3. Render child spans using _render_children():
    #    - This recursively renders the tree with proper indentation
    #
    # 4. Add a blank line + metadata section if trace.metadata exists
    #
    # 5. Join all lines, print the result, and return it
    pass


def _render_children(trace: Trace, parent: Span, prefix: str, total_ms: float) -> list:
    """
    Recursively render child spans with tree-drawing characters.

    Args:
        trace: The trace object
        parent: The parent span whose children to render
        prefix: Current indentation prefix (for nested levels)
        total_ms: Total trace duration for percentage calculation

    Returns:
        List of formatted strings, one per span
    """
    # TODO: Implement recursive child rendering:
    #
    # 1. Get children of parent using trace.get_child_spans(parent)
    # 2. For each child:
    #    a. Determine if it's the last child in the list
    #    b. Choose connector: "└── " for last child, "├── " for others
    #    c. Build the span info string:
    #       - "[{duration}ms] {name}"
    #       - If span has "model" attribute, append " ({model}, {total_tokens} tokens)"
    #       - If span has "tool_name" attribute, append " ({tool_name})"
    #       - Append percentage: "  {pct}%"
    #    d. Color the line using get_span_color()
    #    e. Color the percentage in GRAY
    #    f. Add the formatted line to results
    #    g. Recursively render this child's children with updated prefix:
    #       - If last child, new prefix = prefix + "    "
    #       - Otherwise, new prefix = prefix + "│   "
    #
    # 3. Return the list of formatted lines
    pass


# =============================================================================
# JSON EXPORT
# =============================================================================

# WHAT: Export a trace as a JSON object compatible with OpenTelemetry's
#   trace format, suitable for import into Jaeger, Langfuse, etc.
# WHY:  Terminal views are great for debugging, but you often need to
#   ship traces to a backend for querying, alerting, and long-term storage.
# GOTCHA: The exported JSON uses microsecond timestamps (not seconds)
#   to match OpenTelemetry conventions.

def render_trace_json(trace: Trace, output_path: Optional[str] = None) -> dict:
    """
    Export a trace as OpenTelemetry-compatible JSON.

    Args:
        trace: The trace to export
        output_path: Optional file path to write the JSON to

    Returns:
        The trace as a dict
    """
    # TODO: Implement JSON export:
    #
    # 1. Build the trace dict:
    #    {
    #      "trace_id": trace.trace_id,
    #      "name": trace.name,
    #      "duration_ms": trace.get_duration_ms(),
    #      "metadata": trace.metadata,
    #      "spans": [... one dict per span ...]
    #    }
    #
    # 2. For each span, create a dict with:
    #    - "span_id", "trace_id", "parent_span_id"
    #    - "name", "status"
    #    - "start_time_unix_us": int(span.start_time * 1_000_000)
    #    - "end_time_unix_us": int(span.end_time * 1_000_000)
    #    - "duration_ms": span.duration_ms
    #    - "attributes": span.attributes
    #    - "events": span.events
    #
    # 3. If output_path is given, write the dict as formatted JSON to file
    #
    # 4. Return the dict
    pass


# =============================================================================
# SELF-TEST
# =============================================================================

def self_test():
    """Render a mock trace in the terminal and export to JSON."""
    print("=" * 60)
    print("M19 Trace Viewer — Self-Test")
    print("=" * 60)
    print()

    # Create an instrumented mock agent and run it
    logger = StructuredLogger(service_name="ucc_agent", min_level="WARN")
    agent = MockUCCAgent()
    instrumented = InstrumentedAgent(agent, logger)
    result, trace = instrumented.run("Find all UCC filings for Greenfield Logistics in New York")

    # Render the trace as a tree
    print("\n--- Terminal Trace View ---\n")
    rendered = render_trace(trace)

    # Export to JSON
    print("\n--- JSON Export ---\n")
    output_dir = os.path.join(os.path.dirname(__file__), "..", "expected_output")
    os.makedirs(output_dir, exist_ok=True)
    json_path = os.path.join(output_dir, "trace_export.json")
    trace_json = render_trace_json(trace, output_path=json_path)
    print(f"Trace exported to: {json_path}")
    print(f"Spans in export: {len(trace_json['spans'])}")
    print(f"Trace duration:  {trace_json['duration_ms']:.1f} ms")
    print()

    # Verify
    assert rendered is not None, "render_trace should return a string"
    assert len(rendered) > 0, "Rendered trace should not be empty"
    assert len(trace_json["spans"]) == 4, f"Expected 4 spans in JSON, got {len(trace_json['spans'])}"
    print("All assertions passed!")


if __name__ == "__main__":
    self_test()
