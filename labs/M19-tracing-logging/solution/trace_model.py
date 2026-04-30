"""
M19 Lab — Trace Data Model (Solution)
======================================
Complete trace/span data model compatible with OpenTelemetry concepts.

Usage:
    python trace_model.py
"""

import uuid
import time
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timezone


# =============================================================================
# SPAN
# =============================================================================

@dataclass
class Span:
    """A single unit of work within a trace."""

    name: str
    trace_id: str
    span_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    parent_span_id: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    attributes: dict = field(default_factory=dict)
    events: list = field(default_factory=list)
    status: str = "ok"

    def set_attribute(self, key: str, value) -> None:
        """Set a key-value attribute on this span."""
        self.attributes[key] = value

    def add_event(self, name: str, attributes: Optional[dict] = None) -> None:
        """Record a timestamped event (e.g., an error or milestone)."""
        self.events.append({
            "name": name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "attributes": attributes or {}
        })

    def finish(self) -> None:
        """Mark the span as finished — set end_time and calculate duration_ms."""
        self.end_time = time.time()
        self.duration_ms = round((self.end_time - self.start_time) * 1000, 2)


# =============================================================================
# TRACE
# =============================================================================

class Trace:
    """A collection of spans representing one end-to-end request."""

    def __init__(self, name: str = "trace", metadata: Optional[dict] = None):
        self.trace_id = uuid.uuid4().hex[:16]
        self.name = name
        self.metadata = metadata or {}
        self.spans: list[Span] = []
        self.root_span: Optional[Span] = None

    def create_root_span(self, name: str) -> Span:
        """Create and register the root span for this trace."""
        span = Span(name=name, trace_id=self.trace_id, parent_span_id=None)
        span.start_time = time.time()
        self.root_span = span
        self.spans.append(span)
        return span

    def create_child_span(self, name: str, parent: Span) -> Span:
        """Create a child span under the given parent span."""
        span = Span(name=name, trace_id=self.trace_id, parent_span_id=parent.span_id)
        span.start_time = time.time()
        self.spans.append(span)
        return span

    def add_span(self, span: Span) -> None:
        """Register an existing span with this trace."""
        self.spans.append(span)

    def get_duration_ms(self) -> Optional[float]:
        """Get total trace duration from the root span."""
        if self.root_span:
            return self.root_span.duration_ms
        return None

    def get_child_spans(self, parent: Span) -> list:
        """Get all direct children of a given span."""
        return [s for s in self.spans if s.parent_span_id == parent.span_id]


# =============================================================================
# SPAN CONTEXT
# =============================================================================

class SpanContext:
    """Context manager for automatic span timing and error capture."""

    def __init__(self, trace: Trace, name: str, parent: Optional[Span] = None):
        self.trace = trace
        self.name = name
        self.parent = parent
        self.span: Optional[Span] = None

    def __enter__(self) -> Span:
        if self.parent is None:
            self.span = self.trace.create_root_span(self.name)
        else:
            self.span = self.trace.create_child_span(self.name, self.parent)
        return self.span

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.span.status = "error"
            self.span.add_event("exception", {
                "type": exc_type.__name__,
                "message": str(exc_val)
            })
        self.span.finish()
        return False


# =============================================================================
# SELF-TEST
# =============================================================================

def self_test():
    """Create a sample trace with nested spans to verify the data model."""
    print("=" * 60)
    print("M19 Trace Model — Self-Test")
    print("=" * 60)

    trace = Trace(name="ucc_research_agent", metadata={"query": "Find filings for Acme Corp"})

    with SpanContext(trace, "agent_request") as root:
        root.set_attribute("query", "Find filings for Acme Corp")

        with SpanContext(trace, "llm_call", parent=root) as llm_span:
            llm_span.set_attribute("model", "claude-sonnet-4-6")
            llm_span.set_attribute("input_tokens", 350)
            llm_span.set_attribute("output_tokens", 120)
            time.sleep(0.05)

        with SpanContext(trace, "tool_execution", parent=root) as tool_span:
            tool_span.set_attribute("tool_name", "search_filings")
            tool_span.set_attribute("input", {"debtor_name": "Acme Corp"})
            time.sleep(0.02)
            tool_span.set_attribute("output_records", 3)

        with SpanContext(trace, "llm_call", parent=root) as llm_span2:
            llm_span2.set_attribute("model", "claude-sonnet-4-6")
            llm_span2.set_attribute("input_tokens", 800)
            llm_span2.set_attribute("output_tokens", 200)
            time.sleep(0.03)

    print(f"\nTrace ID:    {trace.trace_id}")
    print(f"Trace Name:  {trace.name}")
    print(f"Total Spans: {len(trace.spans)}")
    print(f"Duration:    {trace.get_duration_ms():.1f} ms")
    print()

    for span in trace.spans:
        indent = "  " if span.parent_span_id else ""
        print(f"{indent}Span: {span.name}")
        print(f"{indent}  ID:       {span.span_id}")
        print(f"{indent}  Parent:   {span.parent_span_id or 'None (root)'}")
        print(f"{indent}  Duration: {span.duration_ms:.1f} ms")
        print(f"{indent}  Status:   {span.status}")
        if span.attributes:
            print(f"{indent}  Attrs:    {span.attributes}")
        print()

    children = trace.get_child_spans(trace.root_span)
    print(f"Root span has {len(children)} children")
    assert len(trace.spans) == 4, f"Expected 4 spans, got {len(trace.spans)}"
    assert len(children) == 3, f"Expected 3 children, got {len(children)}"
    assert trace.root_span.status == "ok", "Root span should be ok"
    print("\nAll assertions passed!")


if __name__ == "__main__":
    self_test()
