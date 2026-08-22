"""Phase-level session state.

A modernization gets interrupted: the laptop sleeps, the container restarts,
someone stops the run when phase 3's hit-policy justification looks wrong.
Re-running phases 1 and 2 to reach phase 4 costs real money and real minutes.

Deliberately coarse. State is recorded per PHASE, not per artifact. Resuming
mid-phase would mean knowing exactly which artifacts had been written and which
half-written, and pretending to that precision is worse than restarting the
phase.
"""

from __future__ import annotations

import copy
import json
import os
from datetime import datetime, timezone


class ModernizationSession:
    def __init__(self, path: str):
        self.path = path
        self.state: dict = {"phases": {}, "started_at": self._now()}

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    # -------------------------------------------------------------- io
    def load(self) -> None:
        if not os.path.exists(self.path):
            return
        try:
            with open(self.path, encoding="utf-8") as fh:
                self.state = json.load(fh)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"[session] could not read {self.path} ({exc}); starting fresh")

    def save(self) -> None:
        try:
            os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
            self.state["saved_at"] = self._now()
            with open(self.path, "w", encoding="utf-8") as fh:
                json.dump(self.state, fh, indent=2, default=str)
        except OSError as exc:
            print(f"[session] WARNING: could not save state to {self.path}: {exc}")

    # ---------------------------------------------------------- phases
    def complete(self, phase: str, detail: dict | None = None) -> None:
        self.state.setdefault("phases", {})[phase] = {
            "status": "complete",
            "at": self._now(),
            "detail": detail or {},
        }
        self.save()

    def fail(self, phase: str, error: str) -> None:
        self.state.setdefault("phases", {})[phase] = {
            "status": "failed", "at": self._now(), "error": error[:1000],
        }
        self.save()

    def is_complete(self, phase: str) -> bool:
        return self.state.get("phases", {}).get(phase, {}).get("status") == "complete"

    def completed_phases(self) -> list[str]:
        return [p for p, v in self.state.get("phases", {}).items()
                if v.get("status") == "complete"]

    # ------------------------------------------------------------ fork
    def fork(self, label: str = "fork") -> "ModernizationSession":
        """An independent what-if branch.

        Use it to try the other hit policy -- FIRST instead of UNIQUE -- and
        diff the two divergence reports without contaminating the real run.
        That comparison is one of the more instructive things a student can do
        here, and it should not cost them their state.
        """
        branch = ModernizationSession(self.path.replace(".json", f".{label}.json"))
        branch.state = copy.deepcopy(self.state)
        branch.state["forked_from"] = self.path
        branch.state["forked_at"] = self._now()
        return branch
