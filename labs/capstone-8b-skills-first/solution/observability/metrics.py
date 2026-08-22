"""Rollups over the raw spans, plus a cost estimate.

Prices are per million tokens and are read from the environment so this
file does not go stale when pricing changes. The defaults are a
placeholder order-of-magnitude, not a quote -- check current pricing at
https://claude.com/pricing before you put a number in front of a
stakeholder.
"""

from __future__ import annotations

import os
from collections import defaultdict

from .tracer import Span

OUTPUT_PRICE_PER_MTOK = float(os.environ.get("OUTPUT_PRICE_PER_MTOK", "15.0"))
INPUT_PRICE_PER_MTOK = float(os.environ.get("INPUT_PRICE_PER_MTOK", "3.0"))


def by_phase(spans: list[Span]) -> dict[str, dict]:
    out: dict[str, dict] = defaultdict(lambda: {"count": 0, "tokens": 0, "ms": 0.0, "errors": 0})
    for span in spans:
        bucket = out[span.phase]
        bucket["count"] += 1
        bucket["tokens"] += span.tokens
        bucket["ms"] += span.duration_ms
        if span.error:
            bucket["errors"] += 1
    return {k: dict(v) for k, v in sorted(out.items())}


def slowest(spans: list[Span], n: int = 5) -> list[Span]:
    return sorted(spans, key=lambda s: s.duration_ms, reverse=True)[:n]


def costliest(spans: list[Span], n: int = 5) -> list[Span]:
    return sorted(spans, key=lambda s: s.tokens, reverse=True)[:n]


def estimate_cost(output_tokens: int, input_tokens: int = 0) -> float:
    """Rough USD estimate. Output dominates on this workload -- generated
    DDL and PL/pgSQL bodies are long."""
    return (
        output_tokens / 1_000_000 * OUTPUT_PRICE_PER_MTOK
        + input_tokens / 1_000_000 * INPUT_PRICE_PER_MTOK
    )


def summarize(spans: list[Span]) -> dict:
    total_tokens = sum(s.tokens for s in spans)
    return {
        "spans": len(spans),
        "errors": sum(1 for s in spans if s.error),
        "total_output_tokens": total_tokens,
        "total_ms": round(sum(s.duration_ms for s in spans), 1),
        "estimated_usd": round(estimate_cost(total_tokens), 4),
        "by_phase": by_phase(spans),
    }
