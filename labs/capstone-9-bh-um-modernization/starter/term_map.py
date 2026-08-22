"""The term map: what the two systems call the same thing, and where the same
name means two different things.

Both source trees model utilization management. Neither was written with the
other in mind, so the vocabulary diverged — and it diverged in TWO ways, which
carry opposite risks:

    A. DIFFERENT NAME, SAME CONCEPT
       `notes` and `CLINICAL_NARRATIVE`; `outbox_event` and `BH_AUTH_QUEUE`.
       The risk is MISSING the mapping: you build a duplicate concept, or you
       drop a field because nothing on the other side looked like it.
       This kind announces itself. The names differ, so you go looking.

    B. SAME NAME, DIFFERENT SEMANTICS
       `APPROVED` is a status in both systems. In the clinical platform it is
       terminal. In behavioral health an approved authorization re-enters
       review on its cadence.
       The risk is ASSUMING the mapping. A 1:1 map compiles, passes review,
       looks obviously correct, and deletes concurrent review.
       **This kind is silent, and it is the dangerous one.**

So the data structure below makes an unexamined name-identical pair
impossible to record: `same_semantics` has no default. You have to say.

No SDK import — the term map is constructible and testable without an API key.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field

# What kind of thing is being mapped.
ENTITY = "entity"          # a table or an aggregate
FIELD = "field"            # a column or a property
STATUS = "status"          # a value in a state machine
EVENT = "event"            # a message type
PATTERN = "pattern"        # an architectural idiom
ROLE = "role"              # an actor or permission

KINDS = (ENTITY, FIELD, STATUS, EVENT, PATTERN, ROLE)

#: Recorded when one side has no counterpart at all. Not a failure — it is
#: usually the most interesting entry in the map, because it is a capability
#: the target platform has never needed.
NONE = "(none)"


class TermMapError(ValueError):
    """A mapping that would be unsafe to act on."""


@dataclass
class TermMapping:
    kind: str
    clinical: str
    behavioral: str
    #: REQUIRED, NO DEFAULT. The whole point of this module.
    #:
    #: A name-identical pair recorded without answering this is the failure
    #: mode the map exists to prevent, so it cannot be recorded at all.
    same_semantics: bool
    evidence: str
    #: REQUIRED when `same_semantics` is False. What differs, concretely.
    divergence: str = ""
    #: What a port must do about it. Required when semantics diverge.
    action: str = ""
    trap_id: int | None = None

    @property
    def name_identical(self) -> bool:
        return self.clinical.strip().lower() == self.behavioral.strip().lower()

    @property
    def silent_trap(self) -> bool:
        """Same name, different meaning. The dangerous quadrant.

        A 1:1 map of these compiles and passes and is wrong, and nothing in
        the build, the tests or the type system objects.
        """
        return self.name_identical and not self.same_semantics

    @property
    def unmapped(self) -> bool:
        return NONE in (self.clinical, self.behavioral)

    def validate(self) -> None:
        # --------------------------------------------------------------------
        # TODO 32 -- Refuse a mapping that would be unsafe to act on.
        #
        # The two systems model the same domain and named it differently, in two
        # ways that carry OPPOSITE risks:
        #
        #   * different name, same concept -- the risk is MISSING the mapping. It
        #     announces itself: the names differ, so somebody goes looking.
        #   * same name, different meaning -- the risk is ASSUMING the mapping. A
        #     1:1 map compiles, passes review, and deletes concurrent review.
        #     THIS ONE IS SILENT.
        #
        # So refuse: a mapping with no cited evidence; a divergence with no stated
        # HOW; a divergence with no stated ACTION for the port. And an absent
        # counterpart cannot claim identical semantics.
        #
        # Note that `same_semantics` has no default. That is deliberate -- a
        # name-identical pair recorded without answering it is exactly the failure
        # this map exists to prevent.
        #
        # Verify: tests/test_term_mapping.py
        # --------------------------------------------------------------------
        raise NotImplementedError("see the TODO above")

    def to_dict(self) -> dict:
        d = {k: v for k, v in asdict(self).items() if v not in ("", None)}
        d["name_identical"] = self.name_identical
        d["silent_trap"] = self.silent_trap
        return d


@dataclass
class TermMap:
    mappings: list[TermMapping] = field(default_factory=list)

    NONE = NONE

    def add(self, m: TermMapping) -> TermMapping:
        m.validate()
        self.mappings.append(m)
        return m

    def by_kind(self, kind: str) -> list[TermMapping]:
        return [m for m in self.mappings if m.kind == kind]

    def silent_traps(self) -> list[TermMapping]:
        """Same name, different meaning. Read these first."""
        return [m for m in self.mappings if m.silent_trap]

    def renamed(self) -> list[TermMapping]:
        """Different name, same concept."""
        return [m for m in self.mappings
                if not m.name_identical and m.same_semantics and not m.unmapped]

    def unmapped(self) -> list[TermMapping]:
        return [m for m in self.mappings if m.unmapped]

    # ------------------------------------------------------------- checks

    def acceptance_problems(self, *, required_statuses: set[str] | None = None,
                            required_terms: set[str] | None = None) -> list[str]:
        # --------------------------------------------------------------------
        # TODO 33 -- Say why this term map would not pass.
        #
        # The one that matters: a map with NO same-name-different-meaning entries
        # has compared spellings rather than semantics. Both systems use SUBMITTED,
        # IN_REVIEW, APPROVED, DENIED and PENDED; four of those five do not mean
        # the same thing on both sides.
        #
        # Also require that every value in the donor's status enum is accounted
        # for -- the ones that match by name are precisely the ones that get mapped
        # without being read.
        # --------------------------------------------------------------------
        raise NotImplementedError("see the TODO above")

    # ---------------------------------------------------------------- io

    def to_dict(self) -> dict:
        return {
            "mappings": [m.to_dict() for m in self.mappings],
            "counts": {
                "total": len(self.mappings),
                "silent_traps": len(self.silent_traps()),
                "renamed": len(self.renamed()),
                "unmapped": len(self.unmapped()),
            },
            "acceptance_problems": self.acceptance_problems(),
        }

    def save(self, path: str) -> str:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(self.to_dict(), fh, indent=2)
        return path

    @classmethod
    def load(cls, path: str) -> "TermMap":
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
        tm = cls()
        allowed = set(TermMapping.__annotations__)
        for m in doc.get("mappings", []):
            tm.mappings.append(TermMapping(
                **{k: v for k, v in m.items() if k in allowed}))
        return tm

    def render(self) -> str:
        lines = ["TERM MAP", "=" * 74, ""]
        c = self.to_dict()["counts"]
        lines.append(f"  {c['total']} mappings   "
                     f"{c['silent_traps']} silent traps   "
                     f"{c['renamed']} renamed   "
                     f"{c['unmapped']} with no counterpart")
        lines.append("")

        traps = self.silent_traps()
        lines.append(f"-- SAME NAME, DIFFERENT MEANING ({len(traps)}) " + "-" * 30)
        lines.append("   Read these first. A 1:1 map of any of them compiles,")
        lines.append("   passes, and is wrong.")
        lines.append("")
        for m in traps:
            lines.append(f"  [{m.kind}] {m.clinical}")
            lines.append(f"      diverges : {m.divergence}")
            lines.append(f"      action   : {m.action}")
            lines.append(f"      evidence : {m.evidence}")
            if m.trap_id:
                lines.append(f"      guards   : trap {m.trap_id}")
            lines.append("")

        lines.append(f"-- NO COUNTERPART ({len(self.unmapped())}) " + "-" * 46)
        for m in self.unmapped():
            side = "behavioral only" if m.clinical == NONE else "clinical only"
            name = m.behavioral if m.clinical == NONE else m.clinical
            lines.append(f"  [{m.kind}] {name}  ({side})")
            lines.append(f"      {m.divergence}")
            lines.append(f"      action   : {m.action}")
            lines.append("")

        lines.append(f"-- RENAMED ({len(self.renamed())}) " + "-" * 52)
        for m in self.renamed():
            lines.append(f"  [{m.kind}] {m.clinical:<28} -> {m.behavioral}")
        lines.append("")

        for p in self.acceptance_problems():
            lines.append(f"  * {p}")
        return "\n".join(lines)
