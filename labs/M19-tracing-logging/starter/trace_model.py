"""
M19 Lab — Trace Data Model (Starter)
=====================================
Build a trace/span data model from scratch, compatible with
OpenTelemetry concepts. No external tracing libraries needed.

KEY CONCEPT: A *trace* is one end-to-end request. A *span* is
one unit of work inside that trace (an API call, a tool execution,
a database query). Spans nest: a root span contains child spans,
forming a tree that shows exactly what happened and how long each
part took.

Usage:
    python trace_model.py
"""

import uuid
import time
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timezone


# =============================================================================
# SPAN — one unit of work inside a trace
# =============================================================================

# WHAT: A span captures a single operation: its name, timing, attributes,
#   and any events (like errors) that occurred during execution.
# WHY:  Spans are the building blocks of traces. Each API call, tool
#   execution, or processing step becomes its own span so you can see
#   exactly where time was spent and where errors occurred.
# GOTCHA: span_id and trace_id should be generated automatically.
#   parent_span_id links a child span to its parent — root spans have
#   parent_span_id = None.

@dataclass
class Span:
    """A single unit of work within a trace."""

    name: str
    trace_id: str
    span_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    parent_span_id: Optional[str] = None
    start_time: Optional[float] = None       # time.time() epoch seconds
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    attributes: dict = field(default_factory=dict)
    events: list = field(default_factory=list)
    status: str = "ok"  # "ok" or "error"

    def set_attribute(self, key: str, value) -> None:
        """Set a key-value attribute on this span."""
        # TODO: Store the key-value pair in self.attributes
        pass

    def add_event(self, name: str, attributes: Optional[dict] = None) -> None:
        """Record a timestamped event (e.g., an error or milestone)."""
        # TODO: Append a dict to self.events with:
        #   - "name": the event name
        #   - "timestamp": current ISO-8601 timestamp
        #   - "attributes": the attributes dict (default to {})
        pass

    def finish(self) -> None:
        """Mark the span as finished — set end_time and calculate duration_ms."""
        # TODO:
        # 1. Set self.end_time to current time.time()
        # 2. Calculate self.duration_ms from (end_time - start_time) * 1000
        #    Round to 2 decimal places.
        pass


# =============================================================================
# TRACE — a collection of spans representing one end-to-end request
# =============================================================================

# WHAT: A trace groups all spans from a single request into one object,
#   with a unique trace_id and a reference to the root span.
# WHY:  Without the trace container, spans would be disconnected log
#   entries. The trace gives them structure — a tree with a root.
# GOTCHA: Always call add_span() to register spans — don't just create
#   Span objects without adding them to the trace.

class Trace:
    """A collection of spans representing one end-to-end request."""

    def __init__(self, name: str = "trace", metadata: Optional[dict] = None):
        # TODO: Initialize the following attributes:
        # - self.trace_id: a unique hex string (use uuid.uuid4().hex[:16])
        # - self.name: the trace name
        # - self.metadata: the metadata dict (default to {})
        # - self.spans: an empty list to hold all spans
        # - self.root_span: None (will be set by create_root_span)
        pass

    def create_root_span(self, name: str) -> Span:
        """Create and register the root span for this trace."""
        # TODO:
        # 1. Create a Span with the given name, self.trace_id, and
        #    parent_span_id=None
        # 2. Set span.start_time to current time.time()
        # 3. Store it as self.root_span
        # 4. Add it to self.spans
        # 5. Return the span
        pass

    def create_child_span(self, name: str, parent: Span) -> Span:
        """Create a child span under the given parent span."""
        # TODO:
        # 1. Create a Span with the given name, self.trace_id, and
        #    parent_span_id = parent.span_id
        # 2. Set span.start_time to current time.time()
        # 3. Add it to self.spans
        # 4. Return the span
        pass

    def add_span(self, span: Span) -> None:
        """Register an existing span with this trace."""
        self.spans.append(span)

    def get_duration_ms(self) -> Optional[float]:
        """Get total trace duration from the root span."""
        # TODO: Return self.root_span.duration_ms if root_span exists,
        # otherwise return None
        pass

    def get_child_spans(self, parent: Span) -> list:
        """Get all direct children of a given span."""
        # TODO: Return a list of spans whose parent_span_id matches
        # parent.span_id
        pass


# =============================================================================
# SPAN CONTEXT — context manager for automatic timing
# =============================================================================

# WHAT: A context manager that auto-starts a span on __enter__ and
#   auto-finishes it on __exit__, including error capture.
# WHY:  Manual start/finish calls are error-prone — especially when
#   exceptions occur. The context manager guarantees every span gets
#   a duration, even if the code inside it throws.
# GOTCHA: If an exception occurs, the span's status should be set to
#   "error" and the exception recorded as an event — but the exception
#   must still be re-raised so the caller sees it.

class SpanContext:
    """Context manager for automatic span timing and error capture."""

    def __init__(self, trace: Trace, name: str, parent: Optional[Span] = None):
        """
        Args:
            trace: The trace this span belongs to
            name: Human-readable name for the span
            parent: Parent span (None = create root span)
        """
        self.trace = trace
        self.name = name
        self.parent = parent
        self.span: Optional[Span] = None

    def __enter__(self) -> Span:
        # TODO:
        # 1. If self.parent is None, call self.trace.create_root_span(self.name)
        # 2. Otherwise, call self.trace.create_child_span(self.name, self.parent)
        # 3. Store the result in self.span
        # 4. Return self.span
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        # TODO:
        # 1. If an exception occurred (exc_type is not None):
        #    a. Set self.span.status to "error"
        #    b. Call self.span.add_event("exception", {"type": str(exc_type.__name__),
        #       "message": str(exc_val)})
        # 2. Call self.span.finish() to set end_time and duration
        # 3. Return False (do not suppress the exception)
        pass


# =============================================================================
# SELF-TEST
# =============================================================================

def self_test():
    """Create a sample trace with nested spans to verify the data model."""
    print("=" * 60)
    print("M19 Trace Model — Self-Test")
    print("=" * 60)

    # Create a trace representing an agent request
    trace = Trace(name="ucc_research_agent", metadata={"query": "Find filings for Acme Corp"})

    # Use SpanContext for the root span
    with SpanContext(trace, "agent_request") as root:
        root.set_attribute("query", "Find filings for Acme Corp")

        # Simulate an LLM call (child span)
        with SpanContext(trace, "llm_call", parent=root) as llm_span:
            llm_span.set_attribute("model", "claude-sonnet-4-6")
            llm_span.set_attribute("input_tokens", 350)
            llm_span.set_attribute("output_tokens", 120)
            time.sleep(0.05)  # simulate latency

        # Simulate a tool execution (child span)
        with SpanContext(trace, "tool_execution", parent=root) as tool_span:
            tool_span.set_attribute("tool_name", "search_filings")
            tool_span.set_attribute("input", {"debtor_name": "Acme Corp"})
            time.sleep(0.02)  # simulate latency
            tool_span.set_attribute("output_records", 3)

        # Simulate a second LLM call (child span)
        with SpanContext(trace, "llm_call", parent=root) as llm_span2:
            llm_span2.set_attribute("model", "claude-sonnet-4-6")
            llm_span2.set_attribute("input_tokens", 800)
            llm_span2.set_attribute("output_tokens", 200)
            time.sleep(0.03)  # simulate latency

    # Print results
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

    # Verify structure
    children = trace.get_child_spans(trace.root_span)
    print(f"Root span has {len(children)} children")
    assert len(trace.spans) == 4, f"Expected 4 spans, got {len(trace.spans)}"
    assert len(children) == 3, f"Expected 3 children, got {len(children)}"
    assert trace.root_span.status == "ok", "Root span should be ok"
    print("\nAll assertions passed!")


if __name__ == "__main__":
    self_test()
