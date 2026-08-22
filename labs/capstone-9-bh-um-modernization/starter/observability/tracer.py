"""One span per phase and per ported artifact.

Deliberately small -- a JSONL file and a context manager, not OpenTelemetry.
The question this has to answer is "which phase produced which artifact, how
long did it take, and what did it cost", and a dependency-free tracer answers
it in a file a student can open.

Spans carry NO artifact CONTENT, only identifiers and counts. A trace file is
another sink, and a sink that accumulates clinical narrative is the leak this
run exists to prevent -- so the narrow interface is the control.
"""

from __future__ import annotations

import json
import os
import time
from contextlib import contextmanager
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone


@dataclass
class Span:
    name: str
    phase: str = ""
    started_at: str = ""
    duration_ms: int = 0
    tokens: int = 0
    status: str = "ok"
    error: str = ""
    # Counts and identifiers only. Never content.
    attributes: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


class Tracer:
    def __init__(self, path: str, *, phase: str = ""):
        self.path = path
        self.phase = phase
        self.spans: list[Span] = []

    @contextmanager
    def span(self, name: str, **attributes):
        s = Span(name=name, phase=self.phase,
                 started_at=datetime.now(timezone.utc).isoformat(),
                 attributes=dict(attributes))
        start = time.monotonic()
        try:
            yield s
        except Exception as exc:                     # noqa: BLE001 - recorded, re-raised
            s.status = "error"
            s.error = f"{type(exc).__name__}: {exc}"[:400]
            raise
        finally:
            s.duration_ms = int((time.monotonic() - start) * 1000)
            self.spans.append(s)
            self._append(s)

    def _append(self, s: Span) -> None:
        try:
            os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
            with open(self.path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(s.to_dict()) + "\n")
        except OSError as exc:
            print(f"[tracer] WARNING: could not append to {self.path}: {exc}")

    # ------------------------------------------------------------ summary
    def total_ms(self) -> int:
        return sum(s.duration_ms for s in self.spans)

    def total_tokens(self) -> int:
        return sum(s.tokens for s in self.spans)

    def failures(self) -> list[Span]:
        return [s for s in self.spans if s.status == "error"]

    def by_phase(self) -> dict[str, dict]:
        out: dict[str, dict] = {}
        for s in self.spans:
            entry = out.setdefault(s.phase or "(none)",
                                   {"spans": 0, "ms": 0, "tokens": 0, "errors": 0})
            entry["spans"] += 1
            entry["ms"] += s.duration_ms
            entry["tokens"] += s.tokens
            if s.status == "error":
                entry["errors"] += 1
        return out
