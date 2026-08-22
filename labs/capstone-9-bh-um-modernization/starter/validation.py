"""The eight parity checks, as pure functions.

No SDK import. Each check takes a directory of emitted files (or a parsed
artifact) and returns findings. That shape matters for two reasons:

  * They are testable without an agent run. A check nobody has ever seen fire
    is not a check.
  * The `parity-validator` subagent calls the same functions a human calls from
    `/validate`, so there is one implementation and two ways to reach it.

FOUR OF THESE ARE EXPECTED TO REPORT NON-ZERO on a naive port: rules
divergence, protected-content leak, narrative round-trip, and consent
atomicity. A clean result on any of them should be read as "suspect the
validator" before "the port is perfect" -- which is why `Check.expected_nonzero`
exists and why the report renders it prominently.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field, asdict

import rules_ir as R

# ---------------------------------------------------------------------------


@dataclass
class Finding:
    where: str
    detail: str
    line: int | None = None

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class Check:
    id: int
    name: str
    #: True for the four checks a NAIVE port trips. A clean result from one of
    #: these is only meaningful once you know the check could have fired.
    expected_nonzero: bool = False
    findings: list[Finding] = field(default_factory=list)
    note: str = ""
    #: How much this check actually looked at -- files scanned, cases run. The
    #: number that distinguishes "found nothing" from "looked at nothing".
    scanned: int = 0
    #: Set False when the inputs cannot exercise what the check is for: a case
    #: set that misses the overlap boundary, an empty emitted tree.
    could_have_fired: bool = True

    @property
    def count(self) -> int:
        return len(self.findings)

    @property
    def suspect(self) -> str:
        """Why a clean result from this check should not be trusted.

        Empty when the result is trustworthy.

        THE SEMANTICS THAT MATTER: clean is not suspicious by itself. A good
        port SHOULD come back clean on all four, and treating that as a failure
        would mean the reference answer could never pass -- which is how a
        check trains people to ignore it.

        Clean is suspicious when the check could not have fired: nothing was
        scanned, or the inputs do not cover the case the check exists for.
        """
        # --------------------------------------------------------------------
        # TODO 25 -- When should a CLEAN result not be trusted?
        #
        # Not merely because it is clean: a good port comes back clean on all four
        # expected-non-zero checks, and treating that as a failure would mean the
        # reference answer could never pass -- which is how a check teaches people
        # to ignore it.
        #
        # Clean is suspicious when the check COULD NOT HAVE FIRED: it scanned
        # nothing, or the inputs cannot exercise what it is for.
        # --------------------------------------------------------------------
        raise NotImplementedError("see the TODO above")

    def to_dict(self) -> dict:
        d = {"id": self.id, "name": self.name, "count": self.count,
             "expected_nonzero": self.expected_nonzero,
             "scanned": self.scanned,
             "findings": [f.to_dict() for f in self.findings]}
        if self.note:
            d["note"] = self.note
        if self.suspect:
            d["suspect"] = self.suspect
        return d


def _walk(root: str, exts: set[str]) -> list[str]:
    out = []
    skip = {"node_modules", ".git", "dist", "target", "__pycache__", ".nx"}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in skip]
        for name in sorted(filenames):
            if os.path.splitext(name)[1] in exts:
                out.append(os.path.join(dirpath, name))
    return out


def _rel(root: str, path: str) -> str:
    return os.path.relpath(path, root).replace(os.sep, "/")


# ---------------------------------------------------------------- check 1


def check_rules_divergence(ir: dict, cases=None) -> Check:
    """Every golden case through both engines."""
    c = Check(1, "rules divergence", expected_nonzero=True)
    cases = list(cases if cases is not None else R.golden_cases())
    c.scanned = len(cases)
    c.could_have_fired = R.covers_overlap(cases)

    if not c.could_have_fired:
        c.note = (
            "THE CASE SET DOES NOT COVER THE BRANCH-7 OVERLAP. A clean result "
            "here proves nothing: the one input that distinguishes a hit-policy "
            "decision from a lucky guess is not being tested.")

    for d in R.diff_engines(ir, cases):
        c.findings.append(Finding(
            where=f"case {d.auth_id}",
            detail=(f"ladder {d.legacy.get('outcome')}/{d.legacy.get('granted_loc')} "
                    f"vs table {d.emitted.get('outcome')}/{d.emitted.get('granted_loc')}"
                    f" [{d.legacy_branch}]" +
                    (f" {d.emitted['error']}" if d.emitted.get("error") else ""))))
    return c


# ---------------------------------------------------------------- check 2

# The clinical free-text field, by whatever name it travels under.
#
# The leading \w* matters: an audit table names its columns `old_narrative` and
# `new_narrative`, and a plain \bnarrative\b does not match inside those,
# because the underscore is a word character. That gap let a narrative column
# in an audit table pass the scan -- which is precisely the sink the legacy
# audit trigger fills, one copy per update, with no consent scope and no expiry.
_NARRATIVE_FIELD = re.compile(
    r"\b\w*(clinical_?narrative|clinicalNarrative|narrative|chief_?complaint|"
    r"clinical_?notes?|hpi|progress_?note)\w*\b", re.I)

_SINKS = [
    ("log", re.compile(
        r"\b(log|logger|LOG|console)\s*\.\s*(info|debug|warn|error|trace|log)\b")),
    ("log", re.compile(r"\bSystem\.out\.print")),
    ("event", re.compile(r"\b(payload|event|envelope|message|producer|emit|publish)\b", re.I)),
    ("search-index", re.compile(r"\b(index|mapping|elastic|opensearch|_source)\b", re.I)),
    ("audit", re.compile(r"\b(audit)\b", re.I)),
    ("error-response", re.compile(r"\b(getMessage|stackTrace|printStackTrace|"
                                  r"toString\(\)|throw new \w*Exception)\b")),
]


def check_protected_content_leak(emit_root: str) -> Check:
    """Every emitted sink, for the clinical free-text field.

    A monolith had one log sink. A decomposed system has one per service plus a
    broker plus an index, so the count going UP is the expected shape of this
    finding rather than a surprise.
    """
    # --------------------------------------------------------------------
    # TODO 26 -- Scan every emitted sink for the clinical field.
    #
    # Logs, event payloads, search mappings, audit columns, error paths.
    #
    # Two things that are easy to miss: a narrative column inside an audit table
    # spans lines, so a line-by-line scan will not see it; and a COMMENT naming
    # the field is how a developer warns the next one, so flagging it teaches
    # the wrong lesson.
    #
    # Verify: tests/test_part2_leak.py
    # --------------------------------------------------------------------
    raise NotImplementedError("see the TODO above")


# ---------------------------------------------------------------- check 3


def check_narrative_roundtrip(emit_root: str) -> Check:
    """The clinical field must survive intake -> COLUMN -> response.

    Asserted against the migration, not against the DTO. A field validated and
    then discarded returns a success status and looks correct from outside --
    which is exactly the reference platform's behaviour and exactly why this
    check exists.
    """
    c = Check(3, "narrative round-trip", expected_nonzero=True)
    if not os.path.isdir(emit_root):
        c.note = f"nothing emitted at {emit_root}"
        return c

    sql_files = _walk(emit_root, {".sql"})
    src_files = _walk(emit_root, {".ts", ".java"})
    c.scanned = len(sql_files) + len(src_files)
    sql = " ".join(_read(p) for p in sql_files)
    has_column = bool(re.search(
        r"\b(clinical_narrative|narrative)\b\s+(text|clob|varchar|character)",
        sql, re.I))

    dto_files = [p for p in src_files
                 if re.search(r"(dto|request|command)", os.path.basename(p), re.I)]
    validated = any(_NARRATIVE_FIELD.search(_read(p)) for p in dto_files)

    entity_files = [p for p in src_files
                    if re.search(r"(entity|domain|model)", p, re.I)]
    persisted = any(_NARRATIVE_FIELD.search(_read(p)) for p in entity_files)

    if validated and not has_column:
        c.findings.append(Finding(
            where="intake DTO / migrations",
            detail="the clinical field is accepted and validated but no migration "
                   "creates a column for it -- the caller gets a success and the "
                   "evidence is discarded. This is the reference platform's "
                   "behaviour, reproduced."))
    elif not has_column:
        c.findings.append(Finding(
            where="migrations",
            detail="no column for the clinical narrative anywhere in the emitted "
                   "schema"))
    if has_column and not persisted:
        c.findings.append(Finding(
            where="entity",
            detail="a column exists but no entity field maps to it"))
    return c


def _read(path: str) -> str:
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return ""


# ---------------------------------------------------------------- check 4


def check_consent_atomicity(emit_root: str, seam_map: dict | None = None) -> Check:
    """No authorization without its consent record -- and is that ENFORCED?

    Two parts, and the second is the one that matters. State can be clean today
    and reachable tomorrow: if the two writes live in different services with no
    compensation, nothing prevents the bad state, it simply has not happened
    yet.
    """
    # --------------------------------------------------------------------
    # TODO 27 -- Is the invariant ENFORCED, or does it merely happen to hold?
    #
    # Two parts, and the second is the one that matters. If the two writes live
    # in different services with no compensation, the state is clean today and
    # reachable tomorrow. Report the mechanism, not just the count.
    # --------------------------------------------------------------------
    raise NotImplementedError("see the TODO above")


# ---------------------------------------------------------------- check 5


def check_workflow(emit_root: str) -> Check:
    """The process must loop, carry a timer, and assign its review task."""
    c = Check(5, "workflow")
    bpmn = _walk(emit_root, {".bpmn"}) if os.path.isdir(emit_root) else []
    if not bpmn:
        c.findings.append(Finding(where="camunda/", detail="no BPMN emitted"))
        return c

    for path in bpmn:
        text = _read(path)
        rel = _rel(emit_root, path)

        edges = []
        for tag in re.findall(r"<(?:\w+:)?sequenceFlow\b[^>]*>", text):
            s = re.search(r'sourceRef="([^"]+)"', tag)
            t = re.search(r'targetRef="([^"]+)"', tag)
            if s and t:
                edges.append((s.group(1), t.group(1)))
        if not _has_cycle(edges):
            c.findings.append(Finding(
                where=rel,
                detail="the process does not loop. An approved behavioral-health "
                       "authorization re-enters review on its cadence; a one-shot "
                       "process cannot express concurrent review."))

        if "timerEventDefinition" not in text:
            c.findings.append(Finding(
                where=rel,
                detail="no timer. The continued-stay cadence is a regulatory "
                       "deadline, and a reminder job is not a deadline."))

        tasks = re.findall(r"<(?:\w+:)?userTask[^>]*\bid=\"([^\"]+)\"", text)
        for task in tasks:
            block = re.search(
                rf"<(?:\w+:)?userTask[^>]*id=\"{re.escape(task)}\".*?</(?:\w+:)?userTask>",
                text, re.S)
            chunk = block.group(0) if block else ""
            if not re.search(r"(candidateGroups|candidateUsers|assignee)=", chunk):
                c.findings.append(Finding(
                    where=f"{rel}:{task}",
                    detail="user task with no assignee or candidate group. Where "
                           "the task encodes reviewer licensure, the missing "
                           "candidate group has deleted the rule while leaving "
                           "the diagram looking complete."))
    return c


def _has_cycle(edges) -> bool:
    graph: dict[str, list[str]] = {}
    for s, t in edges:
        graph.setdefault(s, []).append(t)
    colour: dict[str, int] = {}

    def visit(n: str) -> bool:
        colour[n] = 1
        for nxt in graph.get(n, ()):
            if colour.get(nxt, 0) == 1:
                return True
            if colour.get(nxt, 0) == 0 and visit(nxt):
                return True
        colour[n] = 2
        return False

    return any(colour.get(n, 0) == 0 and visit(n) for n in list(graph))


# ---------------------------------------------------------------- check 6


def check_decision_table(emit_root: str) -> Check:
    """A denial must be reachable, with a diagnosis input and a stated policy."""
    c = Check(6, "decision table")
    dmn = _walk(emit_root, {".dmn"}) if os.path.isdir(emit_root) else []
    if not dmn:
        c.findings.append(Finding(where="camunda/", detail="no DMN emitted"))
        return c

    for path in dmn:
        text = _read(path)
        rel = _rel(emit_root, path)

        if not re.search(r'hitPolicy="\w+"', text):
            c.findings.append(Finding(
                where=rel,
                detail="no hit policy stated. DMN defaults to UNIQUE."))

        outputs = set(re.findall(r"<outputEntry[^>]*>\s*<text>\s*\"?(\w+)\"?", text))
        if "DENIED" not in outputs:
            c.findings.append(Finding(
                where=rel,
                detail=f"no rule can output DENIED (outputs: "
                       f"{sorted(o for o in outputs if o.isupper())}). Denials are "
                       f"the regulated event in behavioral health."))

        inputs = " ".join(re.findall(r"<inputExpression[^>]*>\s*<text>([^<]*)", text))
        if not re.search(r"diagnos|\bdx\b", inputs, re.I):
            c.findings.append(Finding(
                where=rel,
                detail="no diagnosis input -- the engine cannot see what it is "
                       "treating."))
    return c


# ---------------------------------------------------------------- check 7


def check_identity(emit_root: str, legacy_counts: dict | None = None) -> Check:
    """Both identifiers carried, and the plan's used to cross the boundary."""
    c = Check(7, "identity")
    sql = " ".join(_read(p) for p in _walk(emit_root, {".sql"})) \
        if os.path.isdir(emit_root) else ""

    has_carveout = bool(re.search(r"\b\w*member_id\b", sql, re.I))
    has_plan = bool(re.search(r"\bplan_member_id\b", sql, re.I))

    if has_carveout and not has_plan:
        c.findings.append(Finding(
            where="migrations",
            detail="only one member identifier in the emitted schema. The "
                   "carve-out vendor's key and the health plan's key are "
                   "different, and anything crossing to the plan must use the "
                   "plan's. A schema with one opaque identifier accepts either "
                   "without objecting, so a wrong choice matches by luck for "
                   "whichever formats coincide."))

    if legacy_counts and legacy_counts.get("unresolved_to_plan"):
        c.note = (
            f"{legacy_counts['unresolved_to_plan']} legacy members "
            f"({legacy_counts.get('unresolved_pct')}%) have no plan identifier "
            f"at all and cannot be reconciled in either direction.")
    return c


# ---------------------------------------------------------------- check 8


def check_screen_coverage(emit_root: str, inventory: dict | None = None) -> Check:
    """Phase 9B. Every legacy screen routable, every view rule relocated.

    Two halves, and the second is the one a mechanical port fails. A component
    that renders the deny button for everyone looks right, passes any test
    written for it, and is wrong in a way that surfaces as an unlicensed
    determination.
    """
    # --------------------------------------------------------------------
    # TODO 28 (phase 9B) -- Every legacy screen routable, every view rule relocated.
    #
    # Match a route DECLARATION, not a substring: "member" appears in
    # `memberLastName` in half the components.
    #
    # Also catch a numeric comparison against a role bitmask carried over from
    # JSTL -- that was the permissive side of the divergence.
    #
    # Verify: tests/test_screen_coverage.py
    # --------------------------------------------------------------------
    raise NotImplementedError("see the TODO above")


# ---------------------------------------------------------------- check 9


def check_flag_classification(emit_root: str, register: dict | None = None) -> Check:
    """No regulatory control may be gated behind a feature flag.

    A ninth check, beyond the eight the spec enumerates. Trap 7 needed it and
    nothing else covered it -- see the note in the spec's parity-validator
    section.
    """
    c = Check(9, "feature-flag classification")
    if not os.path.isdir(emit_root):
        return c

    # The prefix is OPTIONAL. A leading [A-Z] consumed the first character, so
    # a bare CONSENT_ENABLED did not match while PART2_CONSENT_ENABLED did --
    # meaning the plainest and most likely spelling of the flag was the one
    # this check could not see.
    regulated = re.compile(
        r"\b([A-Z0-9_]*(?:CONSENT|AUDIT|PART2|DISCLOSURE|LICENS|"
        r"SECURITY|AUTHZ|PARITY)[A-Z0-9_]*_ENABLED)\b")

    for path in _walk(emit_root, {".yml", ".yaml", ".ts", ".java", ".json",
                                  ".properties", ".env"}):
        text = _read(path)
        for flag in sorted(set(regulated.findall(text))):
            c.findings.append(Finding(
                where=_rel(emit_root, path),
                detail=f"{flag} gates a regulatory control. A control that can "
                       f"be switched off in configuration is a default, not a "
                       f"control -- a week of false here is an unlawful "
                       f"disclosure, not a slow page."))
    return c


# ---------------------------------------------------------------------------


def check_term_mapping(term_map: dict | None,
                       donor_statuses: set[str] | None = None) -> Check:
    """Check 10. Did the run notice that the two vocabularies collide?

    Two failure modes, and they carry opposite risks:

      * DIFFERENT NAME, SAME CONCEPT -- the risk is missing the mapping. It
        announces itself: the names differ, so somebody goes looking.
      * SAME NAME, DIFFERENT MEANING -- the risk is ASSUMING the mapping. A
        1:1 map compiles, passes review, looks obviously correct, and is
        wrong. Nothing objects.

    So a map with no same-name-different-meaning entries has compared
    spellings rather than semantics, and that is the state this check exists
    to catch.
    """
    c = Check(10, "term mapping")
    if not term_map:
        c.note = "no term map -- the excavate phase did not produce one"
        return c

    mappings = term_map.get("mappings", [])
    c.scanned = len(mappings)
    if not mappings:
        c.findings.append(Finding(where="term-map", detail="the term map is empty"))
        return c

    traps = [m for m in mappings if m.get("silent_trap")]
    if not traps:
        c.findings.append(Finding(
            where="term-map",
            detail="no same-name-different-meaning entries. Both systems use "
                   "SUBMITTED, IN_REVIEW, APPROVED, DENIED and PENDED, and at "
                   "least one of those does not mean the same thing on both "
                   "sides. A map with no silent traps compared spellings, not "
                   "semantics."))

    # Every divergence has to say what a port must DO. A divergence with no
    # action is a note, and notes do not survive a refactor.
    for m in mappings:
        if m.get("same_semantics"):
            continue
        label = f"{m.get('clinical')} -> {m.get('behavioral')}"
        if not str(m.get("divergence") or "").strip():
            c.findings.append(Finding(
                where=label, detail="semantics differ with no stated divergence"))
        if not str(m.get("action") or "").strip():
            c.findings.append(Finding(
                where=label, detail="divergence recorded with no action for the port"))

    # The donor's own status enum, exhaustively. The values that match by name
    # are precisely the ones that get mapped without being read.
    mapped = {m.get("clinical") for m in mappings if m.get("kind") == "status"}
    for status in sorted(donor_statuses or set()):
        if status not in mapped:
            c.findings.append(Finding(
                where=f"status {status}",
                detail="not accounted for in the term map. Every value in the "
                       "target platform's enum needs an explicit verdict, "
                       "including the ones that look identical."))
    return c


# ---------------------------------------------------------------------------


def run_all(emit_root: str, *, ir: dict | None = None,
            seam_map: dict | None = None, register: dict | None = None,
            legacy_counts: dict | None = None, inventory: dict | None = None,
            term_map: dict | None = None, donor_statuses: set[str] | None = None,
            phase: str = "all") -> dict:
    """Run the checks. `phase` is "9a", "9b" or "all".

    Check 8 belongs to phase 9B and is gated on 9A being green, so running it
    against a backend-only workspace would report a missing client as a defect
    rather than as work not yet done.
    """
    checks = [
        check_rules_divergence(ir) if ir else Check(
            1, "rules divergence", expected_nonzero=True,
            note="no rules IR -- the extract-rules phase did not complete"),
        check_protected_content_leak(emit_root),
        check_narrative_roundtrip(emit_root),
        check_consent_atomicity(emit_root, seam_map),
        check_workflow(emit_root),
        check_decision_table(emit_root),
        check_identity(emit_root, legacy_counts),
        check_flag_classification(emit_root, register),
        check_term_mapping(term_map, donor_statuses),
    ]
    if phase in ("9b", "all"):
        checks.insert(7, check_screen_coverage(emit_root, inventory))

    blocking = []
    for c in checks:
        # A clean result blocks only when the check COULD NOT HAVE FIRED. A
        # good port is supposed to come back clean on all four; treating that
        # as a failure would mean the reference answer could never pass, which
        # is how a check teaches people to ignore it.
        if c.suspect:
            blocking.append(f"check {c.id} ({c.name}): {c.suspect}")
        if c.count:
            blocking.append(f"check {c.id} ({c.name}): {c.count} findings")

    return {
        "checks": [c.to_dict() for c in checks],
        "verdict": "NOT READY" if blocking else "READY FOR REVIEW",
        "blocking": blocking,
    }


def save(result: dict, path: str) -> str:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2)
    return path
