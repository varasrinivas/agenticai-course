"""Phase-level session state.

A schema migration is the kind of job that gets interrupted: the laptop
sleeps, the container restarts, someone hits Ctrl-C when phase 3 looks
wrong. Re-running phases 1 and 2 to get back to phase 4 costs real money
and real minutes, so state is persisted between phases.

Deliberately coarse. State is recorded per PHASE, not per row. Resuming
mid-load is a correctness problem (you would need to know exactly which
batch committed), and pretending otherwise would be worse than restarting
the phase.
"""

from __future__ import annotations

import copy
import json
import os
from datetime import datetime, timezone


class MigrationSession:
    def __init__(self, path: str):
        self.path = path
        self.state: dict = {"phases": {}, "started_at": self._now()}

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    # ------------------------------------------------------------ io
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

    # --------------------------------------------------------- phases
    def complete(self, phase: str, detail: dict | None = None) -> None:
        self.state.setdefault("phases", {})[phase] = {
            "status": "complete",
            "at": self._now(),
            "detail": detail or {},
        }
        self.save()

    def is_complete(self, phase: str) -> bool:
        return self.state.get("phases", {}).get(phase, {}).get("status") == "complete"

    def completed_phases(self) -> list[str]:
        return [p for p, v in self.state.get("phases", {}).items()
                if v.get("status") == "complete"]

    # ----------------------------------------------------------- fork
    def fork(self) -> "MigrationSession":
        """An independent what-if branch.

        Use it to try an alternative type mapping -- numeric(12,0) instead
        of bigint, say -- without contaminating the real run's state.
        """
        branch = MigrationSession(self.path.replace(".json", ".fork.json"))
        branch.state = copy.deepcopy(self.state)
        branch.state["forked_from"] = self.path
        branch.state["forked_at"] = self._now()
        return branch
