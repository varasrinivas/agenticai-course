"""
Tracer — span-based distributed tracing for the agent system.

Implements a simplified OpenTelemetry-style tracing system:
- Traces represent a complete request lifecycle
- Spans represent individual operations (agent calls, tool calls, LLM calls)
- Spans have parent/child relationships forming a tree
- Each span tracks: timing, token counts, model used, status
"""

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime


@dataclass
class Span:
    """A single span representing one operation in a trace."""
    span_id: str
    trace_id: str
    parent_id: Optional[str]
    name: str                     # e.g., "router_agent.route", "filing_agent.search_filings"
    kind: str                     # "agent", "tool", "llm", "internal"
    start_time: float             # time.time()
    end_time: Optional[float] = None
    status: str = "in_progress"   # "in_progress", "ok", "error"
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def duration_ms(self) -> Optional[float]:
        """Duration in milliseconds."""
        if self.end_time is None:
            return None
        return (self.end_time - self.start_time) * 1000

    def set_attribute(self, key: str, value: Any) -> None:
        """Set a span attribute."""
        self.attributes[key] = value

    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
        """Add a timestamped event to the span."""
        self.events.append({
            "name": name,
            "timestamp": time.time(),
            "attributes": attributes or {},
        })


class Tracer:
    """
    Traces requests through the agent system.

    Creates and manages spans that form a trace tree showing
    exactly what happened during a request — which agents were called,
    which tools they used, how long each step took, and how many tokens
    were consumed.
    """

    def __init__(self):
        self._traces: Dict[str, List[Span]] = {}  # trace_id → list of spans
        self._active_spans: Dict[str, Span] = {}   # span_id → active span

    # ------------------------------------------------------------------
    # TODO 1: Implement start_trace()
    # Create a new trace with a root span.
    # Steps:
    #   1. Generate a trace_id using uuid.uuid4().hex[:16]
    #   2. Create a root Span with:
    #      - span_id = uuid.uuid4().hex[:16]
    #      - trace_id = the generated trace_id
    #      - parent_id = None
    #      - name = the given name
    #      - kind = "internal"
    #      - start_time = time.time()
    #   3. Store in self._traces[trace_id] = [span]
    #   4. Store in self._active_spans[span_id] = span
    #   5. Return the trace_id
    # ------------------------------------------------------------------
    def start_trace(self, name: str) -> str:
        """Start a new trace and return the trace_id."""
        # TODO: Create trace with root span
        pass

    # ------------------------------------------------------------------
    # TODO 2: Implement start_span()
    # Create a child span within an existing trace.
    # Steps:
    #   1. Generate a span_id
    #   2. Create a Span with the given parameters
    #   3. Add to self._traces[trace_id]
    #   4. Add to self._active_spans
    #   5. Return the span_id
    # ------------------------------------------------------------------
    def start_span(
        self,
        trace_id: str,
        name: str,
        kind: str = "internal",
        parent_id: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Start a new span within a trace."""
        # TODO: Create and register span
        pass

    # ------------------------------------------------------------------
    # TODO 3: Implement end_span()
    # End an active span.
    # Steps:
    #   1. Look up span in self._active_spans
    #   2. Set end_time = time.time()
    #   3. Set status = the given status (default "ok")
    #   4. Remove from self._active_spans
    # ------------------------------------------------------------------
    def end_span(self, span_id: str, status: str = "ok") -> None:
        """End an active span."""
        # TODO: Finalize the span
        pass

    # ------------------------------------------------------------------
    # TODO 4: Implement end_trace()
    # End all remaining active spans in the trace and mark it complete.
    # End spans in reverse order (children before parents).
    # ------------------------------------------------------------------
    def end_trace(self, trace_id: str) -> None:
        """End a trace and all its active spans."""
        # TODO: End all active spans belonging to this trace
        pass

    # ------------------------------------------------------------------
    # TODO 5: Implement get_trace()
    # Return all spans for a given trace_id.
    # ------------------------------------------------------------------
    def get_trace(self, trace_id: str) -> List[Span]:
        """Get all spans for a trace."""
        # TODO: Return spans from self._traces
        pass

    # ------------------------------------------------------------------
    # TODO 6: Implement format_trace()
    # Format a trace as a human-readable string showing the span tree.
    # Use indentation to show parent/child relationships.
    # For each span, show:
    #   [status] name (duration_ms ms) [kind] {key attributes}
    # Example:
    #   [ok] request.process (1523.4 ms) [internal]
    #     [ok] router_agent.route (45.2 ms) [agent]
    #     [ok] filing_agent.process (1234.5 ms) [agent]
    #       [ok] llm.call (890.1 ms) [llm] model=claude-sonnet-4-6 tokens=1234
    #       [ok] search_filings (123.4 ms) [tool]
    # ------------------------------------------------------------------
    def format_trace(self, trace_id: str) -> str:
        """Format a trace as a human-readable tree string."""
        # TODO: Build indented trace tree string
        pass

    # ------------------------------------------------------------------
    # TODO 7: Implement get_trace_summary()
    # Return a summary dict for a trace:
    #   - trace_id, total_duration_ms, span_count
    #   - spans_by_kind: {kind: count}
    #   - total_llm_tokens: sum of tokens from LLM spans
    #   - total_llm_calls: count of LLM spans
    #   - error_count: count of spans with status "error"
    # ------------------------------------------------------------------
    def get_trace_summary(self, trace_id: str) -> Dict[str, Any]:
        """Get summary statistics for a trace."""
        # TODO: Compute trace summary
        pass
