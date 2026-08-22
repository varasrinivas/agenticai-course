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
    # --------------------------------------------------------------------
    # TODO 1 -- Transcribe the legacy ladder.
    #
    # Read db/03_PKG_LOC_RULES.sql alongside this function. It is a STATEFUL
    # FIRST-MATCH LADDER: it mutates a running score across branches, some
    # branches commit and return, others adjust and fall through, and branch
    # ORDER is load-bearing.
    #
    # Keep the branch numbers in your comments. The one classification that
    # matters: branch 3's `dim1 >= 4` arm COMMITS, and its `dim1 == 3` arm
    # ACCUMULATES. One source branch, two kinds.
    #
    # Then TODO 2: LocRulesService.evaluate() is a SECOND layer that runs after
    # this one has already returned. Call it from here. It can only downgrade or
    # pend, never upgrade -- reproduce that asymmetry.
    #
    # Verify: tests/test_rules_hit_policy.py
    # --------------------------------------------------------------------
    raise NotImplementedError("see the TODO above")


def _apply_java_layer(case: Case, d: Decision) -> Decision:
    """LocRulesService.evaluate -- the second layer.

    Runs AFTER the ladder has committed, so it can only downgrade or pend,
    never upgrade. That asymmetry is load-bearing and must survive translation.

    It also reads inputs the PL/SQL never saw, two of which live in other
    teams' schemas and are outside this system's change control.
    """
    # --------------------------------------------------------------------
    # TODO 2 -- The second rules layer.
    #
    # src/main/java/com/bridgeway/bhauth/service/LocRulesService.java
    #
    # Three adjustments, applied AFTER the ladder has committed:
    #   A  benefit cap      -- caps units WITHOUT changing the level
    #   B  frequency pend   -- and read the 2016 compliance note above it
    #   C  network step-down
    #
    # It reads inputs the PL/SQL never saw, two of which live in other teams'
    # schemas. Skip this layer and three of twelve golden cases come back wrong
    # -- and wrong plausibly.
    # --------------------------------------------------------------------
    raise NotImplementedError("see the TODO above")


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
    # --------------------------------------------------------------------
    # TODO 3 -- Evaluate a flattened decision table under a hit policy.
    #
    # This is what a DMN engine does. Handle FIRST, UNIQUE, PRIORITY, ANY and
    # COLLECT, and raise HitPolicyError when the policy is not stated at all --
    # DMN defaults to UNIQUE, so silence is a production error waiting for the
    # first case that matches two rows.
    #
    # UNIQUE must raise when more than one row matches. That is the honest
    # failure: the table is telling you the ladder's ordering carried
    # information it does not.
    # --------------------------------------------------------------------
    raise NotImplementedError("see the TODO above")


def _derive_inputs(ir: dict, case: Case) -> dict[str, float]:
    """Apply the accumulating branches to produce the derived inputs.

    A running score is a derived INPUT, not a decision. Emitting an
    accumulating branch as a table row produces a table that is subtly and
    permanently wrong.
    """
    # --------------------------------------------------------------------
    # TODO 4 -- Compute the derived inputs.
    #
    # The running score is an INPUT, not a decision. Apply every accumulating
    # branch in order, then the derived flags.
    #
    # Emitting an accumulating branch as a table row is the most common way to
    # produce a table that is subtly and permanently wrong.
    # --------------------------------------------------------------------
    raise NotImplementedError("see the TODO above")


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
    # --------------------------------------------------------------------
    # TODO 5 -- Run every case through both engines and report disagreements.
    #
    # A non-zero result on your first run is expected. Classify each one before
    # you change anything: hit-policy artefact, unconverted layer, misclassified
    # branch, or a deliberate correction.
    # --------------------------------------------------------------------
    raise NotImplementedError("see the TODO above")


def covers_overlap(cases: Iterable[Case]) -> bool:
    """Does this case set contain a case that trips the branch-7 overlap?

    If not, a clean divergence report proves nothing. The validator is required
    to say so rather than reporting a pass.
    """
    # --------------------------------------------------------------------
    # TODO 6 -- Does this case set contain a case that trips the branch-7 overlap?
    #
    # Without one, a clean divergence report proves nothing -- the single input
    # that distinguishes a hit-policy decision from a lucky guess is not being
    # tested. Walk the accumulating branches and check whether any case reaches
    # score >= 10 with dimension 1 >= 3.
    # --------------------------------------------------------------------
    raise NotImplementedError("see the TODO above")


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
