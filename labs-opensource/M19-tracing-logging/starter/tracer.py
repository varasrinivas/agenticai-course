"""
M19 Lab - Step 1: Zero-Dependency JSONL Tracer
===============================================
One TraceEvent schema for all four categories; append-only JSON Lines.
Run smoke test: python tracer.py
"""

import json
import time
import traceback
from dataclasses import asdict, dataclass, field
from typing import Any, Optional


@dataclass
class TraceEvent:
    """(COMPLETE) Unified trace event covering all four agent event categories."""

    # ── Common fields (all events) ──
    category: str          # "tool_call" | "llm_turn" | "loop_iter" | "error"
    run_id: str            # UUID linking all events in one agent run
    ts: float = field(default_factory=time.time)

    # ── Tool call fields ──
    tool_name: Optional[str] = None
    tool_args: Optional[str] = None    # json.dumps(args, default=str)
    tool_output: Optional[str] = None  # truncated to 2048 chars
    tool_ok: Optional[bool] = None
    tool_error: Optional[str] = None

    # ── LLM turn fields ──
    model: Optional[str] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    finish_reason: Optional[str] = None  # stop | tool_calls | length | error
    turn_index: Optional[int] = None

    # ── Agent loop iteration fields ──
    iteration: Optional[int] = None
    tools_invoked: Optional[list] = None
    exit_reason: Optional[str] = None

    # ── Error fields ──
    exc_type: Optional[str] = None
    exc_msg: Optional[str] = None
    stack_tail: Optional[str] = None   # last 3 frames only
    retried: Optional[bool] = None
    retry_count: Optional[int] = None

    # ── Latency (shared) ──
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
        """TODO:
        1. If event.category not in VALID_CATEGORIES:
             raise ValueError(f"Unknown category: {event.category}")
        2. Append event.to_json() + "\\n" to self.filepath (open mode "a",
           encoding="utf-8")
        """
        pass  # Remove this line when you add your code

    def tool_call(self, name: str, args: dict, output: Any,
                  latency_ms: float, ok: bool = True,
                  error: Optional[str] = None) -> None:
        """TODO: emit a "tool_call" TraceEvent.
        - tool_args = json.dumps(args, default=str)
        - tool_output = str(output)[:2048]   ← TRUNCATE: huge outputs bloat traces
        """
        pass  # Remove this line when you add your code

    def llm_turn(self, model: str, prompt_tokens: int, completion_tokens: int,
                 finish_reason: str, latency_ms: float, turn_index: int) -> None:
        """TODO: emit an "llm_turn" TraceEvent with all six fields."""
        pass  # Remove this line when you add your code

    def loop_iter(self, iteration: int, tools: list,
                  exit_reason: str, latency_ms: float) -> None:
        """TODO: emit a "loop_iter" TraceEvent (tools → tools_invoked)."""
        pass  # Remove this line when you add your code

    def error(self, exc: Exception, retried: bool = False, retry_count: int = 0) -> None:
        """TODO: emit an "error" TraceEvent.
        - stack_tail = "".join(traceback.format_tb(exc.__traceback__)[-3:])
          ← LAST 3 FRAMES ONLY; full stacks bloat trace files
        - exc_type = type(exc).__name__, exc_msg = str(exc)
        """
        pass  # Remove this line when you add your code


# ── Smoke test (COMPLETE) ──
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
