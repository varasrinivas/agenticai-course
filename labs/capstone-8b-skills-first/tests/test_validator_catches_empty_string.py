"""The planted bug, and the checks that must find it.

Read `test_a_clean_report_on_a_corrupted_load_is_a_failure` first. It is the
one that inverts the usual polarity: a *clean* result is a failure, because a
validator that reports no defect on a deliberately corrupted load is broken,
and a broken validator is worse than none -- it converts an unknown risk into
a false assurance.

Skills-first note: in the subagent build these functions lived in
`solution/validation.py`, and the *rules* they enforce were prose inside
`.claude/agents/migration-validator.md`. Two places, free to drift. Here both
live in the migration-validation skill, and the load-side rule they check
against lives in nullability-preservation -- which the loading phase reads
too. The tests reach the scripts by path, exactly as an agent would.
"""

from __future__ import annotations

import json

import pytest

from conftest import load_skill_script

_checksums = load_skill_script("migration-validation", "compare_checksums.py")
_nulls = load_skill_script("nullability-preservation", "compare_nulls.py")

BLOCKER = _checksums.BLOCKER
WARNING = _checksums.WARNING
reconcile = _checksums.reconcile
render = _checksums.render
to_summary = _checksums.to_summary
compare_spot_check = _checksums.compare_spot_check
looks_truncated_to_midnight = _checksums.looks_truncated_to_midnight

ColumnVerdict = _nulls.ColumnVerdict
compare_profiles = _nulls.compare_profiles

# The real profile of UCC_DEBTOR, from legacy-oracle/fixtures/.
ORACLE_DEBTOR = {
    "table_name": "UCC_DEBTOR",
    "row_count": 7418,
    "null_debtor_name": 0,
    "null_mailing_address_1": 0,
    "null_mailing_address_2": 1412,
    "null_city": 0,
}

# What a load that forgot null_as produces: the NULLs became empty strings.
PG_DEBTOR_BROKEN = {
    **ORACLE_DEBTOR,
    "null_mailing_address_2": 0,
    "empty_mailing_address_2": 1412,
}

PG_DEBTOR_CLEAN = {**ORACLE_DEBTOR, "empty_mailing_address_2": 0}


# ---------------------------------------------------------- row counts
def test_matching_row_counts_pass():
    report = reconcile("ucc_filing", {"row_count": 5000}, {"row_count": 5000})
    assert not [d for d in report.defects if d.check == "row_count"]


def test_row_count_mismatch_is_a_blocker():
    report = reconcile("ucc_filing", {"row_count": 5000}, {"row_count": 4998})
    defect = next(d for d in report.defects if d.check == "row_count")
    assert defect.severity == BLOCKER
    assert "2 rows" in defect.consequence


# --------------------------------------------------------- null counts
def test_matching_null_counts_pass():
    report = reconcile("ucc_debtor", ORACLE_DEBTOR, PG_DEBTOR_CLEAN)
    assert report.defects == []


def test_null_divergence_is_a_blocker():
    report = reconcile("ucc_debtor", ORACLE_DEBTOR, PG_DEBTOR_BROKEN)
    defect = next(d for d in report.defects if d.check == "null_count")
    assert defect.severity == BLOCKER
    assert defect.column == "mailing_address_2"


def test_known_source_drift_downgrades_to_warning():
    """Drift that exists in Oracle is not a migration defect.

    Reporting it as a BLOCKER is its own failure -- a validator that cries
    wolf is one people learn to skip.
    """
    report = reconcile(
        "ucc_filing",
        {"row_count": 10, "null_status": 3},
        {"row_count": 10, "null_status": 1, "empty_status": 0},
        source_drift={"null_status"},
    )
    assert all(d.severity == WARNING for d in report.defects)


# ------------------------------------------------- the empty-string trap
def test_empty_strings_are_a_blocker_even_when_counts_match():
    """Oracle has no empty string, so any on the PostgreSQL side were made
    by the load. This holds regardless of whether NULL counts agree."""
    report = reconcile(
        "ucc_filing",
        {"row_count": 10, "null_status": 0},
        {"row_count": 10, "null_status": 0, "empty_status": 5},
    )
    defect = next(d for d in report.defects if d.check == "empty_string_divergence")
    assert defect.severity == BLOCKER


def test_the_planted_defect_is_found():
    report = reconcile("ucc_debtor", ORACLE_DEBTOR, PG_DEBTOR_BROKEN)
    checks = {d.check for d in report.defects}
    assert "empty_string_divergence" in checks
    assert "null_count" in checks


def test_the_defect_names_its_consequence():
    """A defect a reader cannot act on has not been reported."""
    report = reconcile("ucc_debtor", ORACLE_DEBTOR, PG_DEBTOR_BROKEN)
    defect = next(d for d in report.defects if d.check == "empty_string_divergence")
    assert "null_as" in defect.consequence
    assert "IS NULL" in defect.consequence


def test_shared_skill_agrees_with_the_validator():
    """The loader and the validator must not disagree about 'correct'.

    They read the same file, which is the whole argument for making
    nullability-preservation a skill rather than prose in two prompts.
    """
    shared = compare_profiles(ORACLE_DEBTOR, PG_DEBTOR_BROKEN, "ucc_debtor")
    validator = reconcile("ucc_debtor", ORACLE_DEBTOR, PG_DEBTOR_BROKEN)

    shared_columns = {v.column for v in shared.defects}
    validator_columns = {d.column for d in validator.defects if d.column}
    assert shared_columns == validator_columns

    clean_shared = compare_profiles(ORACLE_DEBTOR, PG_DEBTOR_CLEAN, "ucc_debtor")
    assert not clean_shared.defects and not reconcile(
        "ucc_debtor", ORACLE_DEBTOR, PG_DEBTOR_CLEAN).defects


# -------------------------------------------------------- the spot check
def test_spot_check_catches_date_truncation():
    """The defect no aggregate check can see."""
    defects = compare_spot_check(
        "ucc_filing",
        [{"filing_id": 1042, "filed_date": "2019-04-02 14:32:07"}],
        [{"filing_id": 1042, "filed_date": "2019-04-02 00:00:00"}],
        key="filing_id",
    )
    assert len(defects) == 1
    assert "timestamp(0)" in defects[0].consequence


def test_spot_check_passes_identical_rows():
    assert compare_spot_check(
        "ucc_filing",
        [{"filing_id": 1, "filed_date": "2019-04-02 14:32:07"}],
        [{"filing_id": 1, "filed_date": "2019-04-02 14:32:07"}],
        key="filing_id",
    ) == []


def test_spot_check_tolerates_driver_numeric_types():
    """Decimal vs float vs int is a driver artefact, not a defect."""
    assert compare_spot_check(
        "ucc_filing",
        [{"filing_id": 1, "filing_fee": 25}],
        [{"filing_id": 1, "filing_fee": 25.0}],
        key="filing_id",
    ) == []


def test_spot_check_reports_a_missing_row():
    defects = compare_spot_check(
        "ucc_filing", [{"filing_id": 9}], [{"filing_id": 8}], key="filing_id")
    assert defects and defects[0].severity == BLOCKER


@pytest.mark.parametrize("src,tgt,expected", [
    ("2019-04-02 14:32:07", "2019-04-02 00:00:00", True),
    ("2019-04-02 00:00:00", "2019-04-02 00:00:00", False),  # already midnight
    ("2019-04-02 14:32:07", "2019-04-03 00:00:00", False),  # different day
    ("2019-04-02 14:32:07", "2019-04-02 14:32:07", False),  # unchanged
])
def test_midnight_truncation_detector(src, tgt, expected):
    assert looks_truncated_to_midnight(src, tgt) is expected


# ------------------------------------------------------------ reporting
def test_report_never_emits_a_percentage():
    """A percentage is how a data-corruption bug reaches production."""
    report = reconcile("ucc_debtor", ORACLE_DEBTOR, PG_DEBTOR_BROKEN)
    assert "%" not in render([report])


def test_summary_json_has_the_expected_shape():
    report = reconcile("ucc_debtor", ORACLE_DEBTOR, PG_DEBTOR_BROKEN)
    summary = to_summary([report])
    assert set(summary) == {
        "tables_validated", "checks_passed", "checks_failed", "defects"}
    assert summary["checks_failed"] == len(summary["defects"])
    json.dumps(summary)  # must be serialisable as-is


def test_a_clean_report_on_a_corrupted_load_is_a_failure():
    """The inverted test.

    If this ever passes with an empty defect list, the validator has stopped
    working and every downstream 'migration OK' is meaningless. In the
    skills-first architecture the validator runs in the same context that
    performed the load, so this is the failure mode to guard hardest.
    """
    report = reconcile("ucc_debtor", ORACLE_DEBTOR, PG_DEBTOR_BROKEN)
    assert report.defects, (
        "The validator reported no defects on a load that converted 1,412 "
        "Oracle NULLs into empty strings. A validator that misses the planted "
        "bug is worse than no validator at all."
    )
    assert report.checks_failed > 0
