"""
M19 Lab — Trace Viewer (Solution)
==================================
Complete terminal trace viewer and JSON exporter.

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

class Colors:
    """ANSI color codes for terminal output."""
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    GRAY = "\033[90m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

    @staticmethod
    def enabled() -> bool:
        return os.environ.get("NO_COLOR") is None

    @classmethod
    def colorize(cls, text: str, color: str) -> str:
        if cls.enabled():
            return f"{color}{text}{cls.RESET}"
        return text


def get_span_color(span: Span) -> str:
    """Return the appropriate color for a span based on its name/status."""
    if span.status == "error":
        return Colors.RED
    if "llm" in span.name:
        return Colors.BLUE
    if "tool" in span.name:
        return Colors.GREEN
    return Colors.CYAN


# =============================================================================
# TRACE RENDERER
# =============================================================================

def render_trace(trace: Trace) -> str:
    """Render a trace as a colored tree in the terminal."""
    lines = []

    # Header
    duration = trace.get_duration_ms() or 0
    header = f"Trace {trace.trace_id}  |  Total: {duration:.1f}ms  |  {len(trace.spans)} spans"
    lines.append(Colors.colorize(header, Colors.CYAN + Colors.BOLD))
    lines.append(Colors.colorize("-" * len(header), Colors.GRAY))

    # Root span
    if trace.root_span:
        root_text = f"[{trace.root_span.duration_ms:.1f}ms] {trace.root_span.name}"
        lines.append(Colors.colorize(root_text, get_span_color(trace.root_span)))

        # Child spans
        child_lines = _render_children(trace, trace.root_span, "", duration)
        lines.extend(child_lines)

    # Metadata
    if trace.metadata:
        lines.append("")
        lines.append(Colors.colorize("Metadata:", Colors.GRAY))
        for k, v in trace.metadata.items():
            lines.append(Colors.colorize(f"  {k}: {v}", Colors.GRAY))

    result = "\n".join(lines)
    print(result)
    return result


def _render_children(trace: Trace, parent: Span, prefix: str, total_ms: float) -> list:
    """Recursively render child spans with tree-drawing characters."""
    children = trace.get_child_spans(parent)
    lines = []

    for i, child in enumerate(children):
        is_last = (i == len(children) - 1)
        connector = "\u2514\u2500\u2500 " if is_last else "\u251c\u2500\u2500 "

        # Build span info
        info = f"[{child.duration_ms:.1f}ms] {child.name}"

        # Add details based on attributes
        if "model" in child.attributes:
            total_tokens = child.attributes.get("total_tokens", "?")
            info += f" ({child.attributes['model']}, {total_tokens} tokens)"
        elif "tool_name" in child.attributes:
            info += f" ({child.attributes['tool_name']})"

        # Add percentage
        pct = (child.duration_ms / total_ms * 100) if total_ms > 0 else 0
        pct_str = f"  {pct:.1f}%"

        # Colorize
        color = get_span_color(child)
        colored_info = Colors.colorize(f"{prefix}{connector}{info}", color)
        colored_pct = Colors.colorize(pct_str, Colors.GRAY)

        lines.append(f"{colored_info}{colored_pct}")

        # Recurse into children
        child_prefix = prefix + ("    " if is_last else "\u2502   ")
        lines.extend(_render_children(trace, child, child_prefix, total_ms))

    return lines


# =============================================================================
# JSON EXPORT
# =============================================================================

def render_trace_json(trace: Trace, output_path: Optional[str] = None) -> dict:
    """Export a trace as OpenTelemetry-compatible JSON."""
    trace_dict = {
        "trace_id": trace.trace_id,
        "name": trace.name,
        "duration_ms": trace.get_duration_ms(),
        "metadata": trace.metadata,
        "spans": []
    }

    for span in trace.spans:
        span_dict = {
            "span_id": span.span_id,
            "trace_id": span.trace_id,
            "parent_span_id": span.parent_span_id,
            "name": span.name,
            "status": span.status,
            "start_time_unix_us": int(span.start_time * 1_000_000) if span.start_time else None,
            "end_time_unix_us": int(span.end_time * 1_000_000) if span.end_time else None,
            "duration_ms": span.duration_ms,
            "attributes": span.attributes,
            "events": span.events
        }
        trace_dict["spans"].append(span_dict)

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(trace_dict, f, indent=2, default=str)

    return trace_dict


# =============================================================================
# SELF-TEST
# =============================================================================

def self_test():
    """Render a mock trace in the terminal and export to JSON."""
    print("=" * 60)
    print("M19 Trace Viewer — Self-Test")
    print("=" * 60)
    print()

    logger = StructuredLogger(service_name="ucc_agent", min_level="WARN")
    agent = MockUCCAgent()
    instrumented = InstrumentedAgent(agent, logger)
    result, trace = instrumented.run("Find all UCC filings for Greenfield Logistics in New York")

    print("\n--- Terminal Trace View ---\n")
    rendered = render_trace(trace)

    print("\n--- JSON Export ---\n")
    output_dir = os.path.join(os.path.dirname(__file__), "..", "expected_output")
    os.makedirs(output_dir, exist_ok=True)
    json_path = os.path.join(output_dir, "trace_export.json")
    trace_json = render_trace_json(trace, output_path=json_path)
    print(f"Trace exported to: {json_path}")
    print(f"Spans in export: {len(trace_json['spans'])}")
    print(f"Trace duration:  {trace_json['duration_ms']:.1f} ms")
    print()

    assert rendered is not None, "render_trace should return a string"
    assert len(rendered) > 0, "Rendered trace should not be empty"
    assert len(trace_json["spans"]) == 4, f"Expected 4 spans in JSON, got {len(trace_json['spans'])}"
    print("All assertions passed!")


if __name__ == "__main__":
    self_test()
