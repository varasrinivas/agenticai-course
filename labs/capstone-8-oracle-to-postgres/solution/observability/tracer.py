"""Minimal span tracer.

One span per migrated object, so the report can answer "which table cost
the most tokens" and "which conversion took the longest" without anyone
having to re-read a transcript. Deliberately dependency-free -- adding
OpenTelemetry here would be the right call in production and the wrong
call in a lab where the point is to see the mechanism.
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Span:
    label: str
    started_at: str
    duration_ms: float = 0.0
    tokens: int = 0
    error: str | None = None
    attributes: dict = field(default_factory=dict)

    @property
    def phase(self) -> str:
        return self.label.split(":", 1)[0]

    @property
    def target(self) -> str:
        return self.label.split(":", 1)[1] if ":" in self.label else "-"

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "phase": self.phase,
            "target": self.target,
            "started_at": self.started_at,
            "duration_ms": round(self.duration_ms, 1),
            "tokens": self.tokens,
            "error": self.error,
            **self.attributes,
        }


class Tracer:
    def __init__(self) -> None:
        self.spans: list[Span] = []
        self._t0 = time.perf_counter()

    @contextmanager
    def span(self, label: str):
        span = Span(label=label, started_at=datetime.now(timezone.utc).isoformat())
        started = time.perf_counter()
        self.spans.append(span)
        try:
            yield span
        except Exception as exc:            # noqa: BLE001 -- record then re-raise
            span.error = f"{type(exc).__name__}: {exc}"
            raise
        finally:
            span.duration_ms = (time.perf_counter() - started) * 1000

    def finish(self) -> list[Span]:
        return self.spans

    @property
    def wall_ms(self) -> float:
        return (time.perf_counter() - self._t0) * 1000
