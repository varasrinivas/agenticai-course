"""Run metrics.

The one that matters is `coverage`, and it is deliberately reported as a PAIR:
automated, and queued for human decision.

A single "percent automated" figure invites the reading that higher is better,
and for this system higher is worse past a point. BH_AUTH.LEGACY_OVERRIDE has
no surviving documentation and is set on roughly 400 live rows; the correct
handling is the manual-review queue. A run reporting 100% automated has guessed
at it, and the guess changes determinations for real people.

So `coverage_line()` refuses to print a bare percentage when the queue is
empty. It says what happened instead.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict


@dataclass
class Metrics:
    artifacts_emitted: int = 0
    artifacts_queued: int = 0
    gaps_recorded: int = 0
    must_build_new: int = 0
    must_not_port: int = 0
    rules_divergences: int = 0
    protected_content_hits: int = 0
    tool_calls: int = 0
    output_tokens: int = 0
    wall_ms: int = 0
    phase_failures: dict = field(default_factory=dict)

    # ------------------------------------------------------------ coverage
    def total_items(self) -> int:
        return self.artifacts_emitted + self.artifacts_queued

    def automated_pct(self) -> float:
        total = self.total_items()
        return round(100.0 * self.artifacts_emitted / total, 1) if total else 0.0

    def coverage_line(self) -> str:
        """The pair, queue first, with the caveat attached when it applies."""
        if self.total_items() == 0:
            return "coverage: nothing produced"

        queued = self.artifacts_queued
        pct = self.automated_pct()

        if queued == 0:
            return (
                f"coverage: {self.artifacts_emitted} artifacts, "
                f"0 queued for human decision.\n"
                f"  *** A run over this system that queues NOTHING has guessed at "
                f"something. BH_AUTH.LEGACY_OVERRIDE is undocumented, handled in "
                f"two places, and set on roughly 400 live rows. Treat {pct}% "
                f"automated as a finding about the run, not about the system."
            )
        return (
            f"coverage: {queued} queued for human decision, "
            f"{self.artifacts_emitted} automated ({pct}%)"
        )

    # ------------------------------------------------------------ warnings
    def warnings(self) -> list[str]:
        out: list[str] = []
        if self.artifacts_queued == 0:
            out.append("nothing queued for human decision -- see coverage")
        if self.rules_divergences == 0:
            out.append(
                "zero rules divergence. Confirm the golden set contains a case "
                "at the overlap boundary; a case set that misses it cannot "
                "detect a hit-policy error.")
        if self.must_build_new < 4:
            out.append(
                f"only {self.must_build_new} must-build-new entries -- the "
                f"reference platform is thin everywhere behavioral health is "
                f"demanding, so a comfortable register suggests the domain was "
                f"not tested against the architecture.")
        if self.must_not_port == 0:
            out.append("no must-not-port entries")
        if self.protected_content_hits:
            out.append(
                f"{self.protected_content_hits} protected-content blocks fired. "
                f"Expected while reading the legacy tree; check none came from "
                f"generated output.")
        return out

    # ------------------------------------------------------------------ io
    def to_dict(self) -> dict:
        d = asdict(self)
        d["automated_pct"] = self.automated_pct()
        d["coverage"] = self.coverage_line()
        d["warnings"] = self.warnings()
        return d

    def save(self, path: str) -> str:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(self.to_dict(), fh, indent=2)
        return path

    @classmethod
    def from_audit_log(cls, path: str) -> "Metrics":
        """Reconstruct what can be reconstructed from the audit trail alone.

        Useful after a crash, and useful as a cross-check: if the audit log and
        the in-memory metrics disagree about how many tools were called, one of
        them is wrong and it matters which.
        """
        m = cls()
        if not os.path.exists(path):
            return m
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                m.tool_calls += 1
                name = entry.get("tool_name", "")
                if name.endswith("write_artifact") and "written" in entry:
                    m.artifacts_emitted += 1
                elif name.endswith("queue_manual_review"):
                    m.artifacts_queued += 1
                elif name.endswith("record_gap"):
                    m.gaps_recorded += 1
        return m
