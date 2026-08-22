"""The gap register.

This is the distinctive deliverable of the whole run. A working repository is
what an ordinary port produces; the register is what makes this an analysis.

Four verdicts, and the constraints on them are enforced here rather than left
to a prompt:

    port-as-is      copy the reference platform's approach unchanged
    extend          the shape is right, the content is insufficient
    must-build-new  nothing corresponds; someone has to build it
    must-not-port   the reference platform does this and copying it is harmful

`must-not-port` REQUIRES a named harm. That is the verdict people soften, and
softening it is how a defect gets copied with a note attached. If you cannot
name the harm, the verdict is `extend`.

No SDK import: the register has to be constructible and testable without an
API key.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from typing import Iterable

PORT_AS_IS = "port-as-is"
EXTEND = "extend"
MUST_BUILD_NEW = "must-build-new"
MUST_NOT_PORT = "must-not-port"

VERDICTS = (PORT_AS_IS, EXTEND, MUST_BUILD_NEW, MUST_NOT_PORT)

# Acceptance floor, from the spec. A floor, not a target: do not pad, and do
# not stop at four.
MIN_MUST_BUILD_NEW = 4
MIN_MUST_NOT_PORT = 1


class RegisterError(ValueError):
    """An entry that would weaken the register if it were accepted."""


@dataclass
class GapEntry:
    capability: str
    verdict: str
    evidence: str
    # Required for must-not-port. The concrete consequence of copying it --
    # not "is not ideal", but what goes wrong and for whom.
    harm: str = ""
    # Required for must-build-new. What the thing has to do.
    requirement: str = ""
    # Which of the ten traps this entry guards, if any.
    trap_id: int | None = None
    # "agrees" / "not listed" / "they list, we missed", plus their item.
    backlog: str = ""

    def validate(self) -> None:
        if self.verdict not in VERDICTS:
            raise RegisterError(
                f"{self.capability!r}: verdict {self.verdict!r} is not one of {VERDICTS}")
        if not self.evidence.strip():
            raise RegisterError(
                f"{self.capability!r}: every verdict cites evidence. "
                f"'The audit trail is insufficient' is an opinion; "
                f"'no audit table, no createdBy column, no transition history' is a finding.")
        if self.verdict == MUST_NOT_PORT and not self.harm.strip():
            raise RegisterError(
                f"{self.capability!r}: must-not-port requires a NAMED HARM. "
                f"If you cannot name what goes wrong and for whom, the verdict "
                f"is 'extend'.")
        if self.verdict == MUST_BUILD_NEW and not self.requirement.strip():
            raise RegisterError(
                f"{self.capability!r}: must-build-new requires a requirement -- "
                f"what the thing has to do. Without one it is a wish, and the "
                f"synthesizer will defer it.")

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v not in ("", None)}


@dataclass
class GapRegister:
    entries: list[GapEntry] = field(default_factory=list)
    backlog_crosscheck: dict = field(default_factory=lambda: {
        "agreements": [], "we_found_they_did_not": [], "they_list_we_missed": []})

    # -------------------------------------------------------------- build
    def add(self, entry: GapEntry) -> GapEntry:
        entry.validate()
        existing = self.find(entry.capability)
        if existing is not None:
            # Exactly one verdict per capability. Two verdicts for one thing
            # means the synthesizer gets to choose, which is not its job.
            raise RegisterError(
                f"{entry.capability!r} already has verdict {existing.verdict!r}. "
                f"Exactly one verdict per capability.")
        self.entries.append(entry)
        return entry

    def find(self, capability: str) -> GapEntry | None:
        key = capability.strip().lower()
        for e in self.entries:
            if e.capability.strip().lower() == key:
                return e
        return None

    def by_verdict(self, verdict: str) -> list[GapEntry]:
        return [e for e in self.entries if e.verdict == verdict]

    def distribution(self) -> dict[str, int]:
        return {v: len(self.by_verdict(v)) for v in VERDICTS}

    # ------------------------------------------------------------ inspect
    def acceptance_problems(self) -> list[str]:
        """Reasons this register would not pass the run's acceptance criteria.

        Returns strings rather than raising: the coordinator reports them and
        halts, and a list reads better in a report than a traceback.
        """
        problems: list[str] = []
        dist = self.distribution()

        if dist[MUST_BUILD_NEW] < MIN_MUST_BUILD_NEW:
            problems.append(
                f"only {dist[MUST_BUILD_NEW]} must-build-new entries "
                f"(floor is {MIN_MUST_BUILD_NEW}). A register this comfortable "
                f"means the domain was not tested against the architecture -- "
                f"the reference platform is thin everywhere behavioral health "
                f"is demanding.")
        if dist[MUST_NOT_PORT] < MIN_MUST_NOT_PORT:
            problems.append(
                f"no must-not-port entries. The reference platform logs member "
                f"identifiers in cleartext and gates security behind a flag "
                f"that defaults off; at least one of those is harmful here.")
        if not self.entries:
            problems.append("register is empty")
        elif dist[PORT_AS_IS] > len(self.entries) * 0.6:
            problems.append(
                f"{dist[PORT_AS_IS]} of {len(self.entries)} entries are "
                f"port-as-is. That distribution suggests the architecture was "
                f"read and the domain was not.")

        cc = self.backlog_crosscheck
        if not any(cc.get(k) for k in cc):
            problems.append(
                "backlog cross-check is empty. A register that reports only "
                "agreements has been confirmed, not checked -- and one that "
                "reports nothing has not been cross-checked at all.")
        return problems

    def unresolved_traps(self, all_traps: Iterable[int]) -> list[int]:
        covered = {e.trap_id for e in self.entries if e.trap_id is not None}
        return sorted(set(all_traps) - covered)

    # --------------------------------------------------------------- io
    def to_dict(self) -> dict:
        return {
            "entries": [e.to_dict() for e in self.entries],
            "distribution": self.distribution(),
            "backlog_crosscheck": self.backlog_crosscheck,
            "acceptance_problems": self.acceptance_problems(),
        }

    def save(self, path: str) -> str:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(self.to_dict(), fh, indent=2)
        return path

    @classmethod
    def load(cls, path: str) -> "GapRegister":
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
        reg = cls()
        reg.entries = [GapEntry(**{k: v for k, v in e.items() if k in GapEntry.__annotations__})
                       for e in doc.get("entries", [])]
        reg.backlog_crosscheck = doc.get("backlog_crosscheck", reg.backlog_crosscheck)
        return reg

    # -------------------------------------------------------------- text
    def render(self) -> str:
        """The register as a human reads it at the approval gate.

        Ordered by how much a reader needs to see it: what must not be copied,
        then what does not exist yet, then the rest.
        """
        order = [MUST_NOT_PORT, MUST_BUILD_NEW, EXTEND, PORT_AS_IS]
        lines = ["GAP REGISTER", "=" * 72, ""]
        dist = self.distribution()
        lines.append("  " + "   ".join(f"{v}: {dist[v]}" for v in order))
        lines.append("")

        for verdict in order:
            group = self.by_verdict(verdict)
            if not group:
                continue
            lines.append(f"-- {verdict.upper()} ({len(group)}) " + "-" * (48 - len(verdict)))
            for e in group:
                lines.append(f"  {e.capability}")
                lines.append(f"    evidence : {e.evidence}")
                if e.harm:
                    lines.append(f"    HARM     : {e.harm}")
                if e.requirement:
                    lines.append(f"    must do  : {e.requirement}")
                if e.trap_id:
                    lines.append(f"    guards   : trap {e.trap_id}")
                if e.backlog:
                    lines.append(f"    backlog  : {e.backlog}")
                lines.append("")
            lines.append("")

        cc = self.backlog_crosscheck
        lines.append("-- BACKLOG CROSS-CHECK " + "-" * 50)
        lines.append(f"  agreements              : {len(cc.get('agreements', []))}")
        for item in cc.get("agreements", []):
            lines.append(f"      {item}")
        lines.append(f"  we found, they did not  : {len(cc.get('we_found_they_did_not', []))}")
        for item in cc.get("we_found_they_did_not", []):
            lines.append(f"      {item}")
        lines.append(f"  they list, we missed    : {len(cc.get('they_list_we_missed', []))}")
        for item in cc.get("they_list_we_missed", []):
            lines.append(f"      {item}")
        lines.append("")

        problems = self.acceptance_problems()
        if problems:
            lines.append("-- NOT READY " + "-" * 59)
            for p in problems:
                lines.append(f"  * {p}")
        return "\n".join(lines)
