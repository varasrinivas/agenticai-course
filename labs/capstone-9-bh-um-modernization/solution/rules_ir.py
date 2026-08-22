"""The rules intermediate representation, and both engines that evaluate it.

This module is the heart of the lab, and it contains no SDK import on purpose:
the divergence test has to be runnable in CI without an API key.

Two engines live here:

`evaluate_legacy` is a faithful Python transcription of PKG_LOC_RULES.EVAL_LOC
plus the second-layer adjustments in LocRulesService. It is a STATEFUL
FIRST-MATCH LADDER -- it mutates a running score across branches, some branches
commit and return, others adjust and fall through, and branch ORDER is
load-bearing.

`evaluate_ir` evaluates a flattened decision table under a declared hit policy.
That is what a DMN engine does.

Running the same case through both is the whole point. Where they disagree, the
hit policy is doing something the ladder did not, and that disagreement is the
finding -- not a bug to paper over.

WHY TRANSCRIBE THE PL/SQL RATHER THAN CALL ORACLE
There is no Oracle instance in this lab. More importantly, a transcription that
students can read next to the original is worth more than a database
connection: the classification of each branch as committing or accumulating is
visible in the code, and that classification is what the conversion gets wrong.
"""

from __future__ import annotations

import json
import os as _os
from dataclasses import dataclass, field, asdict
from typing import Iterable

from condition import ConditionError
from condition import evaluate as condition_eval
from condition import parse as condition_parse

# ASAM levels, least to most intensive. Used for step-down comparisons.
LADDER = ["1.0", "2.1", "2.5", "3.1", "3.5", "3.7", "4.0"]

# Continued-stay cadence in days. REGULATORY DEADLINES, not reminders, and a
# function of the LEVEL rather than of the units approved -- a 14-day approval
# at 3.5 still comes back in 7 days.
REVIEW_INTERVAL = {
    "4.0": 3, "3.7": 5, "3.5": 7, "3.1": 14,
    "2.5": 14, "2.1": 30, "1.0": 90,
}

RESIDENTIAL = {"3.1", "3.5", "3.7", "4.0"}


def review_interval(loc: str | None) -> int:
    return REVIEW_INTERVAL.get(loc or "", 30)


# ---------------------------------------------------------------------------
# Inputs and outputs
# ---------------------------------------------------------------------------


@dataclass
class Case:
    """One authorization, as both engines see it.

    `dims` is 1-indexed by ASAM dimension; index 0 is unused so the numbers in
    the code match the numbers in the clinical framework.
    """

    auth_id: int
    requested_loc: str
    requested_units: int
    diagnosis_code: str = ""
    service_code: str = ""
    urgency: str = "STANDARD"
    network_status: str = "IN"
    legacy_override: str = "N"
    dims: dict[int, int] = field(default_factory=dict)
    cssrs: int = 0
    # Second-layer inputs. These come from tables the PL/SQL never reads, two of
    # which live in other teams' schemas -- see schema_changes.txt.
    remaining_benefit_days: int | None = None
    prior_denials_rolling_year: int = 0
    in_network_capacity: dict[str, bool] = field(default_factory=dict)

    def dim(self, n: int) -> int:
        return int(self.dims.get(n, 0))

    @classmethod
    def from_dict(cls, d: dict) -> "Case":
        dims = {int(k): int(v) for k, v in (d.get("dims") or {}).items()}
        return cls(
            auth_id=int(d.get("auth_id", 0)),
            requested_loc=str(d.get("requested_loc", "1.0")),
            requested_units=int(d.get("requested_units", 0)),
            diagnosis_code=str(d.get("diagnosis_code", "")),
            service_code=str(d.get("service_code", "")),
            urgency=str(d.get("urgency", "STANDARD")),
            network_status=str(d.get("network_status", "IN")),
            legacy_override=str(d.get("legacy_override", "N")),
            dims=dims,
            cssrs=int(d.get("cssrs", 0)),
            remaining_benefit_days=d.get("remaining_benefit_days"),
            prior_denials_rolling_year=int(d.get("prior_denials_rolling_year", 0)),
            in_network_capacity=dict(d.get("in_network_capacity") or {}),
        )


@dataclass
class Decision:
    outcome: str                      # APPROVED | PENDED | DENIED
    granted_loc: str | None = None
    granted_units: int = 0
    interval_days: int = 0
    reason_code: str | None = None
    # The breadcrumb of branches taken. In the legacy system this is the only
    # decision rationale that exists, and it is discarded after a page render.
    rule_path: str = ""

    def comparable(self) -> tuple:
        """The fields a divergence diff compares. rule_path is excluded --
        two engines can reach the same answer by different routes and that is
        not a divergence."""
        return (self.outcome, self.granted_loc, self.granted_units,
                self.interval_days, self.reason_code)

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Engine 1 -- the legacy ladder
# ---------------------------------------------------------------------------


def evaluate_legacy(case: Case, *, apply_java_layer: bool = True) -> Decision:
    """Transcription of PKG_LOC_RULES.EVAL_LOC, then LocRulesService.evaluate.

    Read this next to db/03_PKG_LOC_RULES.sql. Branch numbers match.

    `apply_java_layer=False` gives the PL/SQL answer alone -- useful for showing
    a student what a port that extracts only the database half produces.
    """
    d = Decision(outcome="", rule_path="")
    score = 0                                   # MUTATED ACROSS BRANCHES
    path: list[str] = []

    # -- BRANCH 0: the undocumented escape hatch (BHA-2291, "per DM request").
    # Commits before anything else is read. Do not guess what it means.
    if case.legacy_override == "Y":
        return Decision(
            outcome="PENDED",
            granted_loc=case.requested_loc,
            granted_units=0,
            interval_days=review_interval(case.requested_loc),
            reason_code="LEGACY_OVR",
            rule_path="B0:override",
        )

    # -- BRANCH 1: network. TERMED commits; OUT penalises and falls through.
    if case.network_status == "TERMED":
        return Decision(
            outcome="DENIED",
            granted_loc=None,
            granted_units=0,
            interval_days=0,
            reason_code="PROV_TERMED",
            rule_path="B1:termed;",
        )
    if case.network_status == "OUT":
        score -= 2
        path.append("B1:oon(-2)")

    # -- BRANCH 2: imminent risk. Accumulating.
    if case.cssrs >= 4:
        score += 6
        path.append("B2:cssrs>=4(+6)")
    elif case.cssrs == 3:
        score += 3
        path.append("B2:cssrs=3(+3)")

    # -- BRANCH 3: withdrawal severity. The >= 4 arm COMMITS; the == 3 arm
    # accumulates. Getting this classification wrong is the single most common
    # conversion error.
    d1 = case.dim(1)
    if d1 >= 4:
        path.append("B3:d1>=4=>4.0")
        return Decision("APPROVED", "4.0", min(case.requested_units, 5),
                        review_interval("4.0"), None, ";".join(path) + ";")
    if d1 == 3:
        score += 4
        path.append("B3:d1=3(+4)")

    # -- BRANCH 4: biomedical + emotional load. Accumulating.
    if case.dim(2) >= 3 or case.dim(3) >= 3:
        score += 3
        path.append("B4:d2|d3>=3(+3)")

    # -- BRANCH 5: relapse potential and recovery environment. Both high is a
    # materially stronger signal than either alone, hence two arms.
    if case.dim(5) >= 4 and case.dim(6) >= 4:
        score += 5
        path.append("B5:d5&d6>=4(+5)")
    elif case.dim(5) >= 3 or case.dim(6) >= 3:
        score += 2
        path.append("B5:d5|d6>=3(+2)")

    # -- BRANCH 6: readiness to change. THIS ONE INVERTS. A low score argues
    # AGAINST residential placement -- see the behavioral-health-um skill.
    if case.dim(4) <= 1:
        score -= 3
        path.append("B6:d4<=1(-3)")

    # -- BRANCH 7: THE OVERLAP.
    # Both conditions can hold at once. score=10 with d1=3 satisfies 7a AND 7b.
    # First-commit ordering picks 7a. Flatten these into an unordered table and
    # the answer depends entirely on the hit policy.
    if score >= 10 and d1 >= 3:
        path.append("B7a:score>=10&d1>=3=>3.7")
        d = Decision("APPROVED", "3.7", min(case.requested_units, 10),
                     review_interval("3.7"), None, ";".join(path) + ";")
    elif score >= 8:
        path.append("B7b:score>=8=>3.5")
        d = Decision("APPROVED", "3.5", min(case.requested_units, 14),
                     review_interval("3.5"), None, ";".join(path) + ";")

    # -- BRANCH 8: step-down levels.
    elif score >= 5:
        path.append("B8:score>=5=>2.5")
        d = Decision("APPROVED", "2.5", min(case.requested_units, 20),
                     review_interval("2.5"), None, ";".join(path) + ";")
    elif score >= 2:
        path.append("B8:score>=2=>2.1")
        d = Decision("APPROVED", "2.1", min(case.requested_units, 30),
                     review_interval("2.1"), None, ";".join(path) + ";")

    # -- BRANCH 9: the member asked for more than the criteria support.
    # This is an ADVERSE DETERMINATION and the engine may NOT issue it: only a
    # physician may deny. It pends instead, and that is a separation-of-duties
    # control, not a missing feature.
    elif case.requested_loc in RESIDENTIAL:
        path.append("B9:req>=3.1,score<2=>PEND")
        d = Decision("PENDED", "1.0", 0, review_interval("1.0"),
                     "CRITERIA_NOT_MET", ";".join(path) + ";")

    # -- BRANCH 10: routine outpatient.
    else:
        path.append("B10:default=>1.0")
        d = Decision("APPROVED", "1.0", min(case.requested_units, 12),
                     review_interval("1.0"), None, ";".join(path) + ";")

    if apply_java_layer:
        d = _apply_java_layer(case, d)
    return d


def _apply_java_layer(case: Case, d: Decision) -> Decision:
    """LocRulesService.evaluate -- the second layer.

    Runs AFTER the ladder has committed, so it can only downgrade or pend,
    never upgrade. That asymmetry is load-bearing and must survive translation.

    It also reads inputs the PL/SQL never saw, two of which live in other
    teams' schemas and are outside this system's change control.
    """
    # -- Adjustment A: benefit maximum. Caps units WITHOUT changing the level,
    # so a member can end up granted 3.5 for zero days. Clinically incoherent,
    # and what the system does.
    if case.remaining_benefit_days is not None and d.granted_units > case.remaining_benefit_days:
        d.granted_units = case.remaining_benefit_days
        d.rule_path += "J:A:benefitcap;"
        if case.remaining_benefit_days == 0:
            d.outcome = "PENDED"
            d.reason_code = "BENEFIT_EXHAUSTED"

    # -- Adjustment B: frequency pend.
    # PARITY: the medical side applies no equivalent frequency-based pend.
    # Flagged by compliance in 2016 and never actioned. Do not port or drop
    # this silently -- escalate it.
    if case.prior_denials_rolling_year >= 3 and d.outcome == "APPROVED":
        d.outcome = "PENDED"
        d.reason_code = "FREQUENCY_REVIEW"
        d.rule_path += "J:B:frequency;"

    # -- Adjustment C: network-adequacy step-down. Runs last and can therefore
    # undo the ladder's decision entirely. Also potentially an NQTL: the
    # med/surg side would authorise out-of-network instead.
    if d.outcome == "APPROVED" and d.granted_loc in RESIDENTIAL:
        if not case.in_network_capacity.get(d.granted_loc, True):
            stepped = _step_down(d.granted_loc)
            d.granted_loc = stepped
            d.interval_days = review_interval(stepped)
            d.rule_path += "J:C:stepdown;"

    return d


def _step_down(loc: str | None) -> str | None:
    if loc in LADDER:
        i = LADDER.index(loc)
        return LADDER[i - 1] if i > 0 else loc
    return loc


# ---------------------------------------------------------------------------
# Engine 2 -- the flattened decision table
# ---------------------------------------------------------------------------

HIT_POLICIES = {"FIRST", "UNIQUE", "PRIORITY", "ANY", "COLLECT"}


class HitPolicyError(RuntimeError):
    """Two rows matched under a policy that forbids it.

    This is not a crash to route around. It is the decision table telling you
    that the ladder's ordering carried information the table does not."""


def evaluate_ir(ir: dict, case: Case) -> Decision:
    """Evaluate a flattened table. This is what a DMN engine does.

    The IR's committing rows become table rows; accumulating branches are NOT
    rows -- they are how a derived input is computed, and are applied here
    before matching.
    """
    policy = (ir.get("hit_policy") or "").upper()
    if policy not in HIT_POLICIES:
        # DMN defaults to UNIQUE, so an unstated policy on an overlapping table
        # is a production error waiting for the first case that matches twice.
        raise HitPolicyError(
            f"hit policy not stated (got {policy!r}). DMN defaults to UNIQUE; "
            f"an unstated policy on an overlapping table fails at evaluation."
        )

    env = _derive_inputs(ir, case)

    matches = []
    for row in ir.get("branches", []):
        if row.get("kind") != "committing":
            continue
        try:
            if _match(row.get("condition", ""), env):
                matches.append(row)
        except _CondError as exc:
            raise HitPolicyError(f"row {row.get('id')}: {exc}") from exc

    if not matches:
        default = ir.get("default")
        if default is None:
            raise HitPolicyError("no row matched and the table declares no default")
        return _finish(ir, case, env, default, rule_id="DEFAULT")

    if policy == "FIRST":
        return _finish(ir, case, env, matches[0])

    if policy == "UNIQUE":
        if len(matches) > 1:
            raise HitPolicyError(
                "UNIQUE hit policy: rows "
                + ", ".join(str(m.get("id")) for m in matches)
                + " all matched. Tighten the lower row with the negation of "
                  "the upper one -- the exclusion was always there, encoded as "
                  "position."
            )
        return _finish(ir, case, env, matches[0])

    if policy == "ANY":
        outs = {json.dumps(m.get("outputs"), sort_keys=True) for m in matches}
        if len(outs) > 1:
            raise HitPolicyError(
                "ANY hit policy: matching rows disagree on their outputs")
        return _finish(ir, case, env, matches[0])

    if policy == "PRIORITY":
        order = ir.get("output_priority") or []
        if not order:
            raise HitPolicyError("PRIORITY hit policy declared with no output_priority list")

        def rank(row):
            loc = (row.get("outputs") or {}).get("loc")
            return order.index(loc) if loc in order else len(order)

        best = min(matches, key=rank)
        return _finish(ir, case, env, best)

    # COLLECT returns every match; a single Decision cannot express that, and
    # pretending otherwise is how a collect table silently becomes a first table.
    raise HitPolicyError(
        "COLLECT hit policy returns every match. The caller has to choose, so "
        "this evaluator will not choose for it."
    )


def _derive_inputs(ir: dict, case: Case) -> dict[str, float]:
    """Apply the accumulating branches to produce the derived inputs.

    A running score is a derived INPUT, not a decision. Emitting an
    accumulating branch as a table row produces a table that is subtly and
    permanently wrong.
    """
    # Booleans arrive as 1/0 because the condition language only compares
    # numbers. That is a deliberate limit: a grammar that cannot call functions
    # cannot be talked into evaluating something it should not.
    dx = (case.diagnosis_code or "").upper()
    block = 0
    if dx.startswith("F") and dx[1:3].isdigit():
        block = int(dx[1:3])

    env: dict[str, float] = {
        "dim1": case.dim(1), "dim2": case.dim(2), "dim3": case.dim(3),
        "dim4": case.dim(4), "dim5": case.dim(5), "dim6": case.dim(6),
        "cssrs": case.cssrs,
        "requested_units": case.requested_units,
        "prior_denials": case.prior_denials_rolling_year,
        "legacy_override": 1.0 if case.legacy_override == "Y" else 0.0,
        "network_termed": 1.0 if case.network_status == "TERMED" else 0.0,
        "network_out": 1.0 if case.network_status == "OUT" else 0.0,
        "requested_residential": 1.0 if case.requested_loc in RESIDENTIAL else 0.0,
        "diagnosis_block": float(block),
    }
    env["score"] = 0.0

    for branch in ir.get("branches", []):
        if branch.get("kind") != "accumulating":
            continue
        try:
            if _match(branch.get("condition", ""), env):
                env["score"] = env["score"] + float(branch.get("delta", 0))
        except _CondError:
            continue

    # Derived flags, computed AFTER the score and in declared order.
    #
    # These exist because a decision-table cell constrains exactly ONE input. A
    # tightened row like `score >= 8 and not (score >= 10 and dim1 >= 3)`
    # couples two inputs in one exclusion and cannot be written as a cell at
    # all -- so the exclusion becomes a named input, and the row tests it.
    #
    # That is not a workaround. Naming the overlap is what makes it visible on
    # the table a clinician reads, instead of hiding in row order.
    for derived in ir.get("derived_inputs", []):
        name = derived.get("name")
        if not name:
            continue
        try:
            env[name] = 1.0 if _match(derived.get("condition", ""), env) else 0.0
        except _CondError:
            env[name] = 0.0
    return env


class _CondError(RuntimeError):
    pass


def _match(condition: str, env: dict[str, float]) -> bool:
    """Evaluate a condition against the environment.

    Parsed, not eval'd: the IR describes legacy rules recovered by a model from
    somebody else's code, and that is not a language this process should be
    executing.
    """
    try:
        return condition_eval(condition_parse(condition), env)
    except ConditionError as exc:
        raise _CondError(str(exc)) from exc


def _finish(ir: dict, case: Case, env: dict, row: dict,
            rule_id: str | None = None) -> Decision:
    """Table row -> decision, then the post-table layer.

    Kept together so no evaluation path can accidentally skip the second layer:
    a port that applies the table alone gets three of the twelve golden cases
    wrong, and gets them wrong plausibly.
    """
    d = _to_decision(row, case, env, rule_id or row.get("id", "?"))
    return apply_post_table_adjustments(ir, case, d)


def _to_decision(row: dict, case: Case, env: dict, rule_id: str) -> Decision:
    out = row.get("outputs") or {}

    units = out.get("units")
    if isinstance(units, str) and units.startswith("min("):
        cap = int(units.rstrip(")").split(",")[-1])
        units = min(case.requested_units, cap)

    loc = out.get("loc")
    # The override branch grants whatever was requested. Spelling that as the
    # literal "requested" keeps the table readable; resolving it here keeps the
    # table from having to know the case.
    if loc == "requested":
        loc = case.requested_loc

    return Decision(
        outcome=out.get("outcome", "APPROVED"),
        granted_loc=loc,
        granted_units=int(units or 0),
        interval_days=int(out["interval_days"]) if out.get("interval_days") is not None
        else review_interval(loc),
        reason_code=out.get("reason_code"),
        rule_path=f"DMN:{rule_id};",
    )


def apply_post_table_adjustments(ir: dict, case: Case, d: Decision) -> Decision:
    """The second rules layer, which is NOT part of the decision table.

    It reads inputs the table has no access to -- a benefit accumulator, a
    rolling denial count, a bed-capacity table, two of which live in other
    teams' schemas -- and it runs AFTER the decision, so it can only downgrade
    or pend.

    Modelling these as table rows would be wrong twice: the table would need
    inputs it cannot have, and the downgrade-only asymmetry would be lost. So
    they stay declared in the IR and applied here, which is also how they have
    to be implemented in the emitted service.
    """
    for adj in ir.get("post_table_adjustments", []):
        ident = adj.get("id")

        if ident == "J:A" and case.remaining_benefit_days is not None:
            if d.granted_units > case.remaining_benefit_days:
                d.granted_units = case.remaining_benefit_days
                d.rule_path += "J:A:benefitcap;"
                if case.remaining_benefit_days == 0:
                    d.outcome = "PENDED"
                    d.reason_code = "BENEFIT_EXHAUSTED"

        elif ident == "J:B":
            if case.prior_denials_rolling_year >= 3 and d.outcome == "APPROVED":
                d.outcome = "PENDED"
                d.reason_code = "FREQUENCY_REVIEW"
                d.rule_path += "J:B:frequency;"

        elif ident == "J:C":
            if d.outcome == "APPROVED" and d.granted_loc in RESIDENTIAL:
                if not case.in_network_capacity.get(d.granted_loc, True):
                    stepped = _step_down(d.granted_loc)
                    d.granted_loc = stepped
                    d.interval_days = review_interval(stepped)
                    d.rule_path += "J:C:stepdown;"
    return d


# ---------------------------------------------------------------------------
# Divergence
# ---------------------------------------------------------------------------


@dataclass
class Divergence:
    auth_id: int
    legacy: dict
    emitted: dict
    legacy_branch: str
    note: str = ""


def diff_engines(ir: dict, cases: Iterable[Case]) -> list[Divergence]:
    """Run every case through both engines and report where they disagree.

    A NON-ZERO result on the first run is expected. A zero result usually means
    the case set does not exercise the overlap boundary, not that the
    conversion is perfect -- see `covers_overlap`.
    """
    out: list[Divergence] = []
    for case in cases:
        legacy = evaluate_legacy(case)
        try:
            emitted = evaluate_ir(ir, case)
        except HitPolicyError as exc:
            out.append(Divergence(case.auth_id, legacy.to_dict(), {"error": str(exc)},
                                  legacy.rule_path, "hit policy rejected the case"))
            continue
        if legacy.comparable() != emitted.comparable():
            out.append(Divergence(case.auth_id, legacy.to_dict(), emitted.to_dict(),
                                  legacy.rule_path))
    return out


def covers_overlap(cases: Iterable[Case]) -> bool:
    """Does this case set contain a case that trips the branch-7 overlap?

    If not, a clean divergence report proves nothing. The validator is required
    to say so rather than reporting a pass.
    """
    for case in cases:
        if case.legacy_override == "Y" or case.network_status == "TERMED":
            continue
        if case.dim(1) >= 4:
            continue
        score = -2 if case.network_status == "OUT" else 0
        score += 6 if case.cssrs >= 4 else (3 if case.cssrs == 3 else 0)
        if case.dim(1) == 3:
            score += 4
        if case.dim(2) >= 3 or case.dim(3) >= 3:
            score += 3
        if case.dim(5) >= 4 and case.dim(6) >= 4:
            score += 5
        elif case.dim(5) >= 3 or case.dim(6) >= 3:
            score += 2
        if case.dim(4) <= 1:
            score -= 3
        if score >= 10 and case.dim(1) >= 3:
            return True
    return False


# ---------------------------------------------------------------------------
# The golden set
# ---------------------------------------------------------------------------

GOLDEN_PATH = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)),
                            "evaluation", "golden_cases.json")


def load_golden(path: str | None = None) -> list[tuple[Case, dict, dict]]:
    """Load the golden set as (case, expected_comparable_dict, metadata).

    Transcribed from bhauthtrack/db/02_seed.sql, where each case's expected
    outcome is stated in a comment above the row. `expected` is the FULL
    system answer -- ladder plus Java layer -- because that is what a port has
    to reproduce.
    """
    with open(path or GOLDEN_PATH, encoding="utf-8") as fh:
        doc = json.load(fh)
    out = []
    for entry in doc.get("cases", []):
        meta = {"note": entry.get("note", ""), "branch": entry.get("branch", "")}
        out.append((Case.from_dict(entry), entry.get("expected", {}), meta))
    return out


def golden_cases(path: str | None = None) -> list[Case]:
    return [c for c, _e, _m in load_golden(path)]
