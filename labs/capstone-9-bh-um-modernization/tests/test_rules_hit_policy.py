"""Trap 1 -- the stateful first-match ladder becomes a decision table.

This is the sharpest test in the lab, and the thing it asserts is NOT "a naive
conversion diverges". A naive conversion under FIRST does not diverge -- it
passes, today, because the rows happen to be in ladder order.

What it asserts is that FIRST passes *only while row order holds*, and that
tightened conditions under UNIQUE are order-independent. That is the difference
between a conversion that is correct and one that is correct by luck.
"""

import copy

import pytest

import rules_ir as R


NAIVE_CONDITIONS = {
    "B0": "legacy_override >= 1",
    "B1": "network_termed >= 1",
    "B3": "dim1 >= 4",
    "B7a": "score >= 10 and dim1 >= 3",
    "B7b": "score >= 8",
    "B8a": "score >= 5",
    "B8b": "score >= 2",
    "B9": "requested_residential >= 1",
    "B10": "score >= -99",
}


def naive(ir):
    """One row per branch, conditions exactly as the ladder writes them, no
    negations. This is what a mechanical conversion produces."""
    d = copy.deepcopy(ir)
    for b in d["branches"]:
        if b["id"] in NAIVE_CONDITIONS:
            b["condition"] = NAIVE_CONDITIONS[b["id"]]
    d["overlaps"] = []
    return d


def sort_rows(ir):
    """Reorder committing rows by id -- what a modeller UI, a merge, or a
    tidy-minded colleague does, and what nothing prevents."""
    d = copy.deepcopy(ir)
    rows = [b for b in d["branches"] if b["kind"] == "committing"]
    rest = [b for b in d["branches"] if b["kind"] != "committing"]
    d["branches"] = rest + sorted(rows, key=lambda b: b["id"])
    return d


# ---------------------------------------------------------------- the trap


def test_golden_set_covers_the_overlap(golden_cases):
    """Without a case at the boundary, a clean divergence report proves nothing."""
    assert R.covers_overlap(golden_cases), (
        "no golden case trips the branch-7 overlap. Every hit-policy test below "
        "would pass vacuously.")


def test_overlap_case_matches_two_naive_rows(reference_ir, golden_cases):
    """Case 500001 satisfies BOTH the 3.7 rule and the 3.5 rule."""
    case = next(c for c in golden_cases if c.auth_id == 500001)
    ir = naive(reference_ir)
    env = R._derive_inputs(ir, case)

    assert env["score"] == 10 and case.dim(1) == 3

    matched = [b["id"] for b in ir["branches"]
               if b["kind"] == "committing" and R._match(b["condition"], env)]
    assert "B7a" in matched and "B7b" in matched, (
        f"expected the 3.7 and 3.5 rules to both match; matched {matched}")


def test_unique_policy_rejects_untightened_rows(reference_ir, golden_cases):
    """UNIQUE is the honest failure: it says two rules matched."""
    ir = naive(reference_ir)
    ir["hit_policy"] = "UNIQUE"
    case = next(c for c in golden_cases if c.auth_id == 500001)
    with pytest.raises(R.HitPolicyError, match="UNIQUE"):
        R.evaluate_ir(ir, case)


def test_first_policy_passes_today(reference_ir, golden_cases):
    """The uncomfortable half of the lesson.

    A naive FIRST table reproduces the ladder exactly -- as long as nobody
    touches the row order. This test exists so the next one means something.
    """
    ir = naive(reference_ir)
    ir["hit_policy"] = "FIRST"
    assert R.diff_engines(ir, golden_cases) == []


def test_first_policy_breaks_when_rows_are_reordered(reference_ir, golden_cases):
    """...and this is why FIRST is not good enough.

    Nothing in DMN, in the modeller, in code review or in CI enforces row
    order. Sorting the rows -- a change with no semantic intent whatsoever --
    silently changes clinical determinations.
    """
    ir = sort_rows(naive(reference_ir))
    ir["hit_policy"] = "FIRST"
    divergences = R.diff_engines(ir, golden_cases)
    assert divergences, (
        "expected reordering to change answers under FIRST. If this passes, the "
        "row order after sorting happens to match the ladder and the test needs "
        "a different permutation.")

    changed = {d.auth_id for d in divergences}
    assert 500001 in changed


def test_tightened_unique_is_order_independent(reference_ir, golden_cases):
    """The reference answer. Same result whatever order the rows are in."""
    assert R.diff_engines(reference_ir, golden_cases) == []
    assert R.diff_engines(sort_rows(reference_ir), golden_cases) == []


def test_reference_conversion_matches_the_ladder_exactly(reference_ir, golden):
    """Every golden case, both engines, field for field."""
    for case, expected, meta in golden:
        emitted = R.evaluate_ir(reference_ir, case)
        legacy = R.evaluate_legacy(case)
        assert emitted.comparable() == legacy.comparable(), (
            f"case {case.auth_id} ({meta['branch']}): "
            f"table {emitted.comparable()} vs ladder {legacy.comparable()}")
        assert legacy.to_dict()["outcome"] == expected["outcome"], (
            f"case {case.auth_id}: the ladder no longer produces the outcome "
            f"recorded in 02_seed.sql")


# ------------------------------------------------------ the two rule layers


def test_plsql_alone_gets_three_cases_wrong(golden):
    """A port that extracts only the database half.

    The Java layer runs after the ladder commits, reads inputs the PL/SQL never
    sees, and can only downgrade or pend. Skip it and three of twelve cases come
    back wrong -- and wrong plausibly, which is worse than wrong obviously.
    """
    wrong = []
    for case, expected, _meta in golden:
        ladder_only = R.evaluate_legacy(case, apply_java_layer=False)
        full = R.evaluate_legacy(case)
        if ladder_only.comparable() != full.comparable():
            wrong.append(case.auth_id)

    assert sorted(wrong) == [500002, 500008, 500012], (
        f"expected the benefit cap, the frequency pend and the network "
        f"step-down to be the three cases the PL/SQL alone gets wrong; got {wrong}")


def test_accumulating_branches_are_not_rows(reference_ir):
    """A running score is a derived input, not a decision.

    Emitting an accumulating branch as a table row is the most common way to
    produce a table that is subtly and permanently wrong.
    """
    committing = {b["id"] for b in reference_ir["branches"]
                  if b["kind"] == "committing"}
    accumulating = {b["id"] for b in reference_ir["branches"]
                    if b["kind"] == "accumulating"}

    assert accumulating, "no accumulating branches -- the ladder has several"
    assert not (committing & accumulating)
    # The dim1 branch splits: >= 4 commits, == 3 accumulates. One source
    # branch, two kinds.
    assert "B3" in committing and "B3b" in accumulating


def test_hit_policy_is_stated_and_justified(reference_ir):
    assert reference_ir.get("hit_policy") in R.HIT_POLICIES
    assert len(reference_ir.get("hit_policy_justification", "")) > 100


def test_unstated_hit_policy_is_an_error(reference_ir, golden_cases):
    """DMN defaults to UNIQUE, so silence is a production error waiting."""
    ir = copy.deepcopy(reference_ir)
    ir.pop("hit_policy")
    with pytest.raises(R.HitPolicyError, match="not stated"):
        R.evaluate_ir(ir, golden_cases[0])


def test_every_overlap_has_a_resolution(reference_ir):
    for o in reference_ir.get("overlaps", []):
        assert o.get("resolution"), f"overlap {o.get('rows')} has no resolution"


# ------------------------------------------------- the coverage guarantee


def test_a_case_set_without_the_overlap_marks_itself_uncoverable(reference_ir,
                                                                 golden_cases):
    """The subtlest false pass available.

    Drop case 500001 and the divergence check comes back clean over eleven
    cases -- proving nothing, because the one input that distinguishes a
    hit-policy decision from a lucky guess is no longer being tested.

    The check has to say so itself rather than reporting a pass.
    """
    import validation

    thinned = [c for c in golden_cases if c.auth_id != R_OVERLAP_CASE]
    assert not R.covers_overlap(thinned)

    check = validation.check_rules_divergence(reference_ir, thinned)
    assert check.count == 0
    assert check.scanned == len(thinned)
    assert not check.could_have_fired
    assert "proves nothing" in check.suspect
    assert "OVERLAP" in check.note


def test_the_full_case_set_is_trustworthy(reference_ir, golden_cases):
    import validation

    check = validation.check_rules_divergence(reference_ir, golden_cases)
    assert check.count == 0
    assert check.could_have_fired
    assert check.suspect == ""


R_OVERLAP_CASE = 500001
