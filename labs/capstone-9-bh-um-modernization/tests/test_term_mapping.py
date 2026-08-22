"""The two systems model the same domain and named it differently.

Two failure modes, and they carry OPPOSITE risks:

  A. DIFFERENT NAME, SAME CONCEPT -- `notes` and `CLINICAL_NARRATIVE`.
     The risk is MISSING the mapping. It announces itself: the names differ,
     so somebody goes looking.

  B. SAME NAME, DIFFERENT MEANING -- `APPROVED` on both sides.
     The risk is ASSUMING the mapping. A 1:1 map compiles, passes review,
     looks obviously correct, and deletes concurrent review.
     **This is the silent one, and it is why this file exists.**

Four of the five statuses in the donor's enum diverge in meaning. Only
`SUBMITTED` maps 1:1.
"""

import pytest

import validation
from term_map import (ENTITY, FIELD, NONE, PATTERN, STATUS, TermMap,
                      TermMapError, TermMapping)

import reference_term_map as RTM


@pytest.fixture(scope="module")
def term_map():
    return RTM.build()


# ------------------------------------------------- the fixtures really collide


def test_both_systems_use_the_same_status_names(reference_root, legacy_root):
    """Read from disk, not asserted from memory.

    This is the premise of the whole file: the enums LOOK interchangeable.
    """
    import os
    import re

    donor = ""
    for dp, dn, fn in os.walk(reference_root):
        dn[:] = [d for d in dn if d != "node_modules"]
        for f in fn:
            if f.endswith((".java", ".ts")):
                donor += open(os.path.join(dp, f), encoding="utf-8",
                              errors="replace").read()
    donor_statuses = set(re.findall(
        r"\b(SUBMITTED|IN_REVIEW|APPROVED|DENIED|PENDED|EXPIRED|APPEALED)\b", donor))

    ddl = open(os.path.join(legacy_root, "db", "01_schema.sql"),
               encoding="utf-8").read()
    legacy_statuses = set(re.findall(
        r"'(SUBMITTED|IN_REVIEW|APPROVED|DENIED|PENDED|EXPIRED)'", ddl))

    shared = donor_statuses & legacy_statuses
    assert shared >= {"SUBMITTED", "IN_REVIEW", "APPROVED", "DENIED", "PENDED"}, (
        f"expected the two enums to overlap on five names; shared={shared}")
    assert "EXPIRED" in legacy_statuses and "EXPIRED" not in donor_statuses


def test_the_free_text_field_is_named_differently_on_each_side(reference_root,
                                                               legacy_root):
    """`notes` and `CLINICAL_NARRATIVE`: same concept, opposite fate."""
    import os

    dto = None
    for dp, dn, fn in os.walk(reference_root):
        dn[:] = [d for d in dn if d != "node_modules"]
        for f in fn:
            if "dto" in f.lower() or "dto" in dp.lower():
                text = open(os.path.join(dp, f), encoding="utf-8",
                            errors="replace").read()
                if "notes" in text:
                    dto = text
    assert dto is not None, "expected the donor's intake DTO to carry `notes`"

    ddl = open(os.path.join(legacy_root, "db", "01_schema.sql"),
               encoding="utf-8").read()
    assert "CLINICAL_NARRATIVE" in ddl and "CLOB" in ddl
    assert "notes" not in ddl.lower().split("bh_auth")[1][:600]


# ----------------------------------------------------- the map itself


def test_the_reference_map_is_complete(term_map):
    problems = term_map.acceptance_problems(required_statuses=RTM.DONOR_STATUSES)
    assert problems == [], problems


def test_every_donor_status_is_accounted_for(term_map):
    """The values that match by name are the ones that get mapped unread."""
    mapped = {m.clinical for m in term_map.by_kind(STATUS)}
    assert RTM.DONOR_STATUSES <= mapped


def test_only_one_status_maps_one_to_one(term_map):
    """Four of five diverge. That ratio is the finding."""
    statuses = [m for m in term_map.by_kind(STATUS)
                if m.clinical in RTM.DONOR_STATUSES]
    identical = [m.clinical for m in statuses if m.same_semantics]
    assert identical == ["SUBMITTED"], (
        f"expected SUBMITTED alone to map 1:1; got {identical}")


def test_approved_is_flagged_as_a_silent_trap(term_map):
    """The sharpest one. Terminal on one side, the loop target on the other."""
    m = next(x for x in term_map.by_kind(STATUS) if x.clinical == "APPROVED")
    assert m.name_identical
    assert not m.same_semantics
    assert m.silent_trap
    assert "RE-ENTERS REVIEW" in m.divergence
    assert m.trap_id == 3


def test_in_review_is_a_dead_enum_value_on_the_donor_side(term_map):
    m = next(x for x in term_map.by_kind(STATUS) if x.clinical == "IN_REVIEW")
    assert m.silent_trap
    assert "NEVER ASSIGNED" in m.evidence
    assert "Dead enum value" in m.divergence


def test_denied_distinguishes_cannot_from_must_not(term_map):
    """'Cannot deny' and 'must not deny here' are not the same defect."""
    m = next(x for x in term_map.by_kind(STATUS) if x.clinical == "DENIED")
    assert m.silent_trap
    assert "must not deny HERE" in m.divergence


def test_the_narrative_field_records_the_opposite_fate(term_map):
    m = next(x for x in term_map.mappings if x.behavioral == "CLINICAL_NARRATIVE")
    assert m.clinical == "notes"
    assert not m.same_semantics
    assert "OPPOSITE" in m.divergence
    assert m.trap_id == 2


def test_the_outbox_pattern_is_recognised_under_a_different_name(term_map):
    """`BH_AUTH_QUEUE` is a transactional outbox that nobody called one."""
    m = next(x for x in term_map.mappings if x.behavioral == "BH_AUTH_QUEUE")
    assert m.clinical == "outbox_event"
    assert m.same_semantics
    assert "would not have called it" in m.evidence


def test_concepts_with_no_counterpart_are_recorded(term_map):
    """Usually the most interesting rows in the map."""
    orphans = {m.behavioral for m in term_map.unmapped() if m.clinical == NONE}
    assert {"BH_LOC_REVIEW", "BH_CONSENT", "BH_ASSESSMENT"} <= orphans


def test_the_undocumented_flag_is_recorded_as_do_not_map(term_map):
    m = next(x for x in term_map.mappings if x.behavioral == "LEGACY_OVERRIDE")
    assert m.clinical == NONE
    assert "DO NOT MAP" in m.action


def test_appeals_is_recorded_as_missing_from_both(term_map):
    """The platform team raised it. Our gap analysis did not."""
    m = next(x for x in term_map.mappings if x.clinical == "APPEALED")
    assert m.behavioral == NONE
    assert "NEITHER system has it" in m.divergence


# ------------------------------------------------------ the refusals


def test_a_mapping_with_no_evidence_is_refused():
    tm = TermMap()
    with pytest.raises(TermMapError, match="cite where each side appears"):
        tm.add(TermMapping(kind=FIELD, clinical="a", behavioral="b",
                           same_semantics=True, evidence=""))


def test_a_divergence_with_no_explanation_is_refused():
    """'Similar but not identical' is not something a synthesizer can act on."""
    tm = TermMap()
    with pytest.raises(TermMapError, match="say HOW"):
        tm.add(TermMapping(kind=STATUS, clinical="APPROVED", behavioral="APPROVED",
                           same_semantics=False, evidence="both enums"))


def test_a_divergence_with_no_action_is_refused():
    """A divergence with no action is a note, and notes do not survive."""
    tm = TermMap()
    with pytest.raises(TermMapError, match="what the port must do"):
        tm.add(TermMapping(kind=STATUS, clinical="APPROVED", behavioral="APPROVED",
                           same_semantics=False, evidence="both enums",
                           divergence="terminal on one side"))


def test_an_absent_counterpart_cannot_claim_identical_semantics():
    tm = TermMap()
    with pytest.raises(TermMapError, match="cannot be identical"):
        tm.add(TermMapping(kind=ENTITY, clinical=NONE, behavioral="BH_CONSENT",
                           same_semantics=True, evidence="no consent concept"))


def test_same_semantics_has_no_default():
    """The whole point of the module.

    A name-identical pair recorded WITHOUT answering the semantics question is
    the failure this map exists to prevent, so it must be impossible to
    construct one by omission.
    """
    with pytest.raises(TypeError):
        TermMapping(kind=STATUS, clinical="APPROVED", behavioral="APPROVED",
                    evidence="both enums")          # no same_semantics


def test_case_differences_still_count_as_name_identical():
    """`member_id` and `MEMBER_ID` are the same name in two conventions.

    A comparison that missed this would let the most dangerous pair in the
    schema through as a harmless rename.
    """
    m = TermMapping(kind=FIELD, clinical="member_id", behavioral="MEMBER_ID",
                    same_semantics=False, evidence="both schemas",
                    divergence="one identifier vs two", action="carry both")
    assert m.name_identical and m.silent_trap


# ---------------------------------------------------------- the check


def test_the_check_passes_the_reference_map(term_map):
    c = validation.check_term_mapping(term_map.to_dict(), RTM.DONOR_STATUSES)
    assert c.count == 0
    assert c.scanned == len(term_map.mappings)


def test_the_check_catches_a_naive_one_to_one_map():
    """THE test. Every status mapped by name, nothing examined.

    This is what a synthesizer produces when it compares spellings, and it is
    exactly what compiles and passes and silently deletes concurrent review.
    """
    naive = {"mappings": [
        {"kind": "status", "clinical": s, "behavioral": s,
         "same_semantics": True, "silent_trap": False}
        for s in sorted(RTM.DONOR_STATUSES)]}
    c = validation.check_term_mapping(naive, RTM.DONOR_STATUSES)
    assert c.count == 1
    assert "compared spellings, not semantics" in c.findings[0].detail


def test_the_check_catches_an_unmapped_status():
    partial = {"mappings": [
        {"kind": "status", "clinical": "APPROVED", "behavioral": "APPROVED",
         "same_semantics": False, "silent_trap": True,
         "divergence": "not terminal", "action": "loop"}]}
    c = validation.check_term_mapping(partial, RTM.DONOR_STATUSES)
    missing = [f.where for f in c.findings if f.where.startswith("status")]
    assert len(missing) == 4


def test_the_check_reports_a_missing_map_rather_than_passing():
    c = validation.check_term_mapping(None, RTM.DONOR_STATUSES)
    assert c.count == 0
    assert "did not produce one" in c.note
