"""
M19 Lab - Step 1: Zero-Dependency JSONL Tracer — SOLUTION
==========================================================
Run smoke test: python tracer.py
"""

import json
import time
import traceback
from dataclasses import asdict, dataclass, field
from typing import Any, Optional


@dataclass
class TraceEvent:
    """Unified trace event covering all four agent event categories."""

    category: str
    run_id: str
    ts: float = field(default_factory=time.time)

    tool_name: Optional[str] = None
    tool_args: Optional[str] = None
    tool_output: Optional[str] = None
    tool_ok: Optional[bool] = None
    tool_error: Optional[str] = None

    model: Optional[str] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    finish_reason: Optional[str] = None
    turn_index: Optional[int] = None

    iteration: Optional[int] = None
    tools_invoked: Optional[list] = None
    exit_reason: Optional[str] = None

    exc_type: Optional[str] = None
    exc_msg: Optional[str] = None
    stack_tail: Optional[str] = None
    retried: Optional[bool] = None
    retry_count: Optional[int] = None

    latency_ms: Optional[float] = None

    def to_json(self) -> str:
        return json.dumps(
            {k: v for k, v in asdict(self).items() if v is not None},
            default=str,
        )


class TraceRecorder:
    """Thin wrapper: build events, append to a JSON Lines file."""

    VALID_CATEGORIES = {"tool_call", "llm_turn", "loop_iter", "error"}

    def __init__(self, run_id: str, filepath: str = "agent_trace.jsonl"):
        self.run_id = run_id
        self.filepath = filepath

    def emit(self, event: TraceEvent) -> None:
        if event.category not in self.VALID_CATEGORIES:
            raise ValueError(f"Unknown category: {event.category}")
        with open(self.filepath, "a", encoding="utf-8") as f:
            f.write(event.to_json() + "\n")

    def tool_call(self, name: str, args: dict, output: Any,
                  latency_ms: float, ok: bool = True,
                  error: Optional[str] = None) -> None:
        self.emit(TraceEvent(
            category="tool_call", run_id=self.run_id,
            tool_name=name,
            tool_args=json.dumps(args, default=str),
            tool_output=str(output)[:2048],  # truncate: huge outputs bloat traces
            tool_ok=ok, tool_error=error,
            latency_ms=latency_ms,
        ))

    def llm_turn(self, model: str, prompt_tokens: int, completion_tokens: int,
                 finish_reason: str, latency_ms: float, turn_index: int) -> None:
        self.emit(TraceEvent(
            category="llm_turn", run_id=self.run_id,
            model=model, prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            finish_reason=finish_reason,
            latency_ms=latency_ms, turn_index=turn_index,
        ))

    def loop_iter(self, iteration: int, tools: list,
                  exit_reason: str, latency_ms: float) -> None:
        self.emit(TraceEvent(
            category="loop_iter", run_id=self.run_id,
            iteration=iteration, tools_invoked=tools,
            exit_reason=exit_reason, latency_ms=latency_ms,
        ))

    def error(self, exc: Exception, retried: bool = False, retry_count: int = 0) -> None:
        # Last 3 frames only — full stacks bloat trace files
        tb = "".join(traceback.format_tb(exc.__traceback__)[-3:])
        self.emit(TraceEvent(
            category="error", run_id=self.run_id,
            exc_type=type(exc).__name__,
            exc_msg=str(exc),
            stack_tail=tb,
            retried=retried, retry_count=retry_count,
        ))


if __name__ == "__main__":
    import os
    import uuid

    path = "smoke_trace.jsonl"
    if os.path.exists(path):
        os.remove(path)

    rec = TraceRecorder(run_id=uuid.uuid4().hex[:8], filepath=path)
    rec.tool_call("get_weather", {"city": "Tokyo"}, {"temp": 22}, 12.5)
    rec.llm_turn("mistral", 120, 45, "tool_calls", 950.0, 1)
    rec.loop_iter(1, ["get_weather"], "continuing", 1100.0)
    try:
        raise ValueError("synthetic failure")
    except ValueError as e:
        rec.error(e)

    with open(path, encoding="utf-8") as f:
        lines = [json.loads(l) for l in f if l.strip()]
    print(f"Wrote {len(lines)} events to {path}")
    assert len(lines) == 4
    assert {l["category"] for l in lines} == {"tool_call", "llm_turn", "loop_iter", "error"}
    assert "stack_tail" in lines[3]
    try:
        rec.emit(TraceEvent(category="bogus", run_id="x"))
        raise AssertionError("emit() accepted an unknown category!")
    except ValueError:
        print("Unknown-category validation works.")
    print("All tracer checks passed.")
