"""The seam map: where the monolith is cut, and what replaces what the cut breaks.

A monolith gets atomicity free -- one database, one transaction manager, one
annotation. Decomposed, the same writes become an HTTP call, a message, a
persist in another schema, an outbox row, another message, and every arrow is a
place the sequence can stop.

The distributed system is not wrong for lacking atomicity. It is wrong if
nobody noticed it was there.

So this module refuses to record a seam that crosses a transactional unit
without an `AtomicityReplacement`. That refusal is the point: a data structure
that cannot represent the omission is more useful than a checklist that can.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict

# How a pair of writes relates. Not every pair in one transaction needs the
# same guarantee, and treating them alike is how the analysis goes wrong.
MUST_BE_ATOMIC = "must-be-atomic"
EVENTUAL_GUARANTEED = "eventual-guaranteed"
EVENTUAL_BEST_EFFORT = "eventual-best-effort"
INDEPENDENT = "independent"

COUPLINGS = (MUST_BE_ATOMIC, EVENTUAL_GUARANTEED, EVENTUAL_BEST_EFFORT, INDEPENDENT)


class SeamError(ValueError):
    """A seam that would silently lose a guarantee."""


@dataclass
class Write:
    table: str
    meaning: str
    # Why this write is inside the transaction. The column most likely to be
    # undocumented, and the one that matters -- look for it in class comments
    # and in the commit that merged the method.
    why_atomic: str = ""


@dataclass
class TransactionalUnit:
    """One @Transactional method and everything it writes."""

    method: str
    writes: list[Write] = field(default_factory=list)
    # Behaviour on failure. Often a user-visible contract -- "everything rolls
    # back and the clinician retypes the narrative" -- that a decomposition
    # changes whether or not anyone decided to.
    failure_behaviour: str = ""

    def tables(self) -> list[str]:
        return [w.table for w in self.writes]


@dataclass
class AtomicityReplacement:
    """What stands in for a transaction that a seam broke.

    All five fields are required. An eventual consistency with no observable
    and no alarm is the same as no guarantee, implemented with more moving
    parts -- so a replacement that cannot fill these in is not a replacement.
    """

    mechanism: str          # "outbox + idempotent consumer keyed on authId"
    window: str             # "under 60s at the configured relay interval"
    observable: str         # the query or metric that shows an unclosed gap
    compensation: str       # what closes it
    alarm: str              # what fires if it stays open past the window

    def problems(self) -> list[str]:
        missing = [f for f in ("mechanism", "window", "observable", "compensation", "alarm")
                   if not str(getattr(self, f, "")).strip()]
        return [f"replacement is missing {f}" for f in missing]


@dataclass
class Seam:
    name: str
    left: str                       # service on one side
    right: str                      # service on the other
    crosses: list[str] = field(default_factory=list)   # transactional unit names
    coupling: str = EVENTUAL_GUARANTEED
    replacement: AtomicityReplacement | None = None
    # Set when the analysis concluded the seam should NOT be cut here.
    rejected_because: str = ""

    def validate(self) -> None:
        if self.coupling not in COUPLINGS:
            raise SeamError(f"{self.name}: coupling {self.coupling!r} not in {COUPLINGS}")

        if self.rejected_because:
            return  # a seam that was considered and rejected needs no replacement

        if self.coupling == MUST_BE_ATOMIC:
            raise SeamError(
                f"{self.name}: coupling is must-be-atomic, so this seam cannot be "
                f"cut here. Either move the seam, or record it as rejected with "
                f"`rejected_because`. Compensation is not available for every "
                f"kind of write -- you cannot un-hold protected content you have "
                f"already held.")

        if self.crosses and self.coupling != INDEPENDENT:
            if self.replacement is None:
                raise SeamError(
                    f"{self.name}: crosses {', '.join(self.crosses)} and states no "
                    f"replacement for the atomicity it breaks. "
                    f"'We will write the second row right after' is not an answer.")
            problems = self.replacement.problems()
            if problems:
                raise SeamError(f"{self.name}: " + "; ".join(problems))

    def to_dict(self) -> dict:
        d = asdict(self)
        if self.replacement is None:
            d.pop("replacement", None)
        if not self.rejected_because:
            d.pop("rejected_because", None)
        return d


@dataclass
class SeamMap:
    units: list[TransactionalUnit] = field(default_factory=list)
    seams: list[Seam] = field(default_factory=list)

    def add_unit(self, unit: TransactionalUnit) -> TransactionalUnit:
        self.units.append(unit)
        return unit

    def add_seam(self, seam: Seam) -> Seam:
        seam.validate()
        self.seams.append(seam)
        return seam

    def unit(self, method: str) -> TransactionalUnit | None:
        for u in self.units:
            if u.method == method:
                return u
        return None

    def accepted_seams(self) -> list[Seam]:
        return [s for s in self.seams if not s.rejected_because]

    def unanalysed_units(self) -> list[str]:
        """Transactional units no seam mentions.

        Not automatically a problem -- a unit wholly inside one service is
        fine. But it must be a conclusion someone reached, not one nobody
        looked at, so the report lists them.
        """
        mentioned = {m for s in self.seams for m in s.crosses}
        return [u.method for u in self.units if u.method not in mentioned]

    def problems(self) -> list[str]:
        out: list[str] = []
        for u in self.units:
            missing = [w.table for w in u.writes if not w.why_atomic.strip()]
            if missing:
                out.append(
                    f"{u.method}: no reason recorded for including "
                    f"{', '.join(missing)} in the transaction. That reason is what "
                    f"decides whether the pair can be split.")
        return out

    def to_dict(self) -> dict:
        return {
            "units": [asdict(u) for u in self.units],
            "seams": [s.to_dict() for s in self.seams],
            "unanalysed_units": self.unanalysed_units(),
            "problems": self.problems(),
        }

    def save(self, path: str) -> str:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(self.to_dict(), fh, indent=2)
        return path

    def render(self) -> str:
        lines = ["SEAM MAP", "=" * 72, ""]
        for u in self.units:
            lines.append(f"  {u.method}  ({len(u.writes)} writes)")
            for w in u.writes:
                why = w.why_atomic or "*** NO REASON RECORDED ***"
                lines.append(f"      {w.table:<24} {w.meaning}")
                lines.append(f"      {'':<24} why atomic: {why}")
            if u.failure_behaviour:
                lines.append(f"      on failure: {u.failure_behaviour}")
            lines.append("")

        for s in self.seams:
            if s.rejected_because:
                lines.append(f"  [REJECTED] {s.name}: {s.left} | {s.right}")
                lines.append(f"      because: {s.rejected_because}")
                lines.append("")
                continue
            lines.append(f"  {s.name}: {s.left} | {s.right}   ({s.coupling})")
            if s.crosses:
                lines.append(f"      crosses: {', '.join(s.crosses)}")
            r = s.replacement
            if r:
                lines.append(f"      mechanism   : {r.mechanism}")
                lines.append(f"      window      : {r.window}")
                lines.append(f"      observable  : {r.observable}")
                lines.append(f"      compensation: {r.compensation}")
                lines.append(f"      alarm       : {r.alarm}")
            lines.append("")

        unanalysed = self.unanalysed_units()
        if unanalysed:
            lines.append("  Transactional units no seam mentions:")
            for m in unanalysed:
                lines.append(f"      {m}")
            lines.append("")
        for p in self.problems():
            lines.append(f"  * {p}")
        return "\n".join(lines)
