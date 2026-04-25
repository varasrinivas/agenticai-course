"""
Tracer — span-based distributed tracing.
(Solution — fully implemented)
"""

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Span:
    span_id: str
    trace_id: str
    parent_id: Optional[str]
    name: str
    kind: str
    start_time: float
    end_time: Optional[float] = None
    status: str = "in_progress"
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def duration_ms(self) -> Optional[float]:
        if self.end_time is None:
            return None
        return (self.end_time - self.start_time) * 1000

    def set_attribute(self, key: str, value: Any) -> None:
        self.attributes[key] = value

    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
        self.events.append({
            "name": name, "timestamp": time.time(),
            "attributes": attributes or {},
        })


class Tracer:
    """Traces requests through the agent system."""

    def __init__(self):
        self._traces: Dict[str, List[Span]] = {}
        self._active_spans: Dict[str, Span] = {}

    def start_trace(self, name: str) -> str:
        trace_id = uuid.uuid4().hex[:16]
        span_id = uuid.uuid4().hex[:16]
        root_span = Span(
            span_id=span_id, trace_id=trace_id, parent_id=None,
            name=name, kind="internal", start_time=time.time(),
        )
        self._traces[trace_id] = [root_span]
        self._active_spans[span_id] = root_span
        return trace_id

    def start_span(
        self, trace_id: str, name: str, kind: str = "internal",
        parent_id: Optional[str] = None, attributes: Optional[Dict[str, Any]] = None,
    ) -> str:
        span_id = uuid.uuid4().hex[:16]
        span = Span(
            span_id=span_id, trace_id=trace_id, parent_id=parent_id,
            name=name, kind=kind, start_time=time.time(),
            attributes=attributes or {},
        )
        if trace_id not in self._traces:
            self._traces[trace_id] = []
        self._traces[trace_id].append(span)
        self._active_spans[span_id] = span
        return span_id

    def end_span(self, span_id: str, status: str = "ok") -> None:
        span = self._active_spans.get(span_id)
        if span:
            span.end_time = time.time()
            span.status = status
            del self._active_spans[span_id]

    def end_trace(self, trace_id: str) -> None:
        if trace_id not in self._traces:
            return
        # End active spans in reverse order (children before parents)
        trace_spans = [s for s in self._traces[trace_id] if s.span_id in self._active_spans]
        for span in reversed(trace_spans):
            self.end_span(span.span_id, status="ok")

    def get_trace(self, trace_id: str) -> List[Span]:
        return self._traces.get(trace_id, [])

    def format_trace(self, trace_id: str) -> str:
        spans = self.get_trace(trace_id)
        if not spans:
            return f"Trace {trace_id} not found."

        # Build parent-child relationships
        children: Dict[Optional[str], List[Span]] = {}
        for span in spans:
            parent = span.parent_id
            if parent not in children:
                children[parent] = []
            children[parent].append(span)

        lines = [f"Trace: {trace_id}"]
        lines.append("-" * 60)

        def render(span_id: Optional[str], depth: int):
            for span in children.get(span_id, []):
                duration = f"{span.duration_ms:.1f}ms" if span.duration_ms is not None else "running"
                indent = "  " * depth
                attrs = ""
                if "model" in span.attributes:
                    attrs += f" model={span.attributes['model']}"
                if "tokens" in span.attributes:
                    attrs += f" tokens={span.attributes['tokens']}"
                if "tool_name" in span.attributes:
                    attrs += f" tool={span.attributes['tool_name']}"
                lines.append(f"{indent}[{span.status}] {span.name} ({duration}) [{span.kind}]{attrs}")
                render(span.span_id, depth + 1)

        render(None, 0)
        return "\n".join(lines)

    def get_trace_summary(self, trace_id: str) -> Dict[str, Any]:
        spans = self.get_trace(trace_id)
        if not spans:
            return {"trace_id": trace_id, "error": "not found"}

        total_duration = None
        if spans[0].duration_ms is not None:
            total_duration = spans[0].duration_ms

        kinds = {}
        total_tokens = 0
        llm_calls = 0
        errors = 0
        for span in spans:
            kinds[span.kind] = kinds.get(span.kind, 0) + 1
            if span.kind == "llm":
                llm_calls += 1
                total_tokens += span.attributes.get("tokens", 0)
            if span.status == "error":
                errors += 1

        return {
            "trace_id": trace_id,
            "total_duration_ms": round(total_duration, 2) if total_duration else None,
            "span_count": len(spans),
            "spans_by_kind": kinds,
            "total_llm_tokens": total_tokens,
            "total_llm_calls": llm_calls,
            "error_count": errors,
        }
