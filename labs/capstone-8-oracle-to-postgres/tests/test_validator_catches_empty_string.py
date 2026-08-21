"""The planted bug, and the check that must find it.

Read the last test in this file first. It is the one that inverts the
usual polarity: a *clean* result is a failure, because a validator that
reports no defect on a deliberately corrupted load is broken, and a broken
validator is worse than none -- it converts an unknown risk into a false
assurance.
"""

from __future__ import annotations

from validation import (
    Severity,
    TableReport,
    compare_null_counts,
    compare_row_counts,
    compare_spot_check,
    detect_empty_string_divergence,
    summarize,
)

COLUMNS = ["debtor_name", "mailing_address_1", "mailing_address_2", "city"]


# ---------------------------------------------------------- row counts
def test_matching_row_counts_pass():
    ok, defect = compare_row_counts("ucc_filing", 5000, 5000)
    assert ok and defect is None


def test_row_count_mismatch_is_a_blocker():
    ok, defect = compare_row_counts("ucc_filing", 5000, 4998)
    assert not ok
    assert defect.severity is Severity.BLOCKER
    assert "-2" in defect.detail


# --------------------------------------------------------- null counts
def test_matching_null_counts_pass():
    oracle = {"null_mailing_address_2": 1400, "null_city": 0}
    postgres = {"null_mailing_address_2": 1400, "null_city": 0}
    results = compare_null_counts("ucc_debtor", ["mailing_address_2", "city"],
                                  oracle, postgres)
    assert all(ok for ok, _ in results)


def test_null_count_mismatch_is_reported_per_column():
    oracle = {"null_mailing_address_2": 1400}
    postgres = {"null_mailing_address_2": 0}
    results = compare_null_counts("ucc_debtor", ["mailing_address_2"],
                                  oracle, postgres)
    ok, defect = results[0]
    assert not ok
    assert "ucc_debtor.mailing_address_2" == defect.object
    assert "1,400" in defect.detail


def test_a_missing_count_is_not_silently_a_pass():
    """If the check never ran, that must not look like success."""
    results = compare_null_counts("ucc_debtor", ["mailing_address_2"], {}, {})
    ok, defect = results[0]
    assert not ok
    assert "did not actually run" in defect.detail


# ------------------------------------------- THE empty-string check
def test_bad_load_is_caught():
    """The exact shape of the planted bug.

    Oracle: 1,400 NULLs in mailing_address_2.
    PostgreSQL after a load with null_as='': 0 NULLs, 1,400 empty strings.
    Row counts match. Checksums would look plausible. Only this check
    notices.
    """
    oracle = {"null_mailing_address_2": 1400}
    postgres = {"null_mailing_address_2": 0, "empty_mailing_address_2": 1400}

    defects = detect_empty_string_divergence(
        "ucc_debtor", ["mailing_address_2"], oracle, postgres
    )

    assert len(defects) == 1
    defect = defects[0]
    assert defect.severity is Severity.BLOCKER
    assert defect.check == "empty_string_divergence"
    assert defect.object == "ucc_debtor.mailing_address_2"
    assert "1,400" in defect.detail
    assert "null_as" in defect.detail


def test_good_load_produces_no_defect():
    oracle = {"null_mailing_address_2": 1400}
    postgres = {"null_mailing_address_2": 1400, "empty_mailing_address_2": 0}
    assert detect_empty_string_divergence(
        "ucc_debtor", ["mailing_address_2"], oracle, postgres
    ) == []


def test_partial_conversion_is_still_a_blocker():
    """Half the NULLs converted is not half a bug."""
    oracle = {"null_mailing_address_2": 1400}
    postgres = {"null_mailing_address_2": 700, "empty_mailing_address_2": 700}
    defects = detect_empty_string_divergence(
        "ucc_debtor", ["mailing_address_2"], oracle, postgres
    )
    assert defects[0].severity is Severity.BLOCKER
    assert "700" in defects[0].detail


def test_genuine_empty_strings_are_a_warning_not_a_blocker():
    """A column that legitimately holds empty strings, with NULL counts
    that reconcile, is not the same defect -- flag it, do not block on it."""
    oracle = {"null_notes": 10}
    postgres = {"null_notes": 10, "empty_notes": 25}
    defects = detect_empty_string_divergence("ucc_amendment", ["notes"],
                                             oracle, postgres)
    assert defects[0].severity is Severity.WARNING


# ----------------------------------------------------------- spot check
def test_spot_check_catches_date_truncation():
    """Row counts match. NULL counts match. Only a value comparison finds
    that Oracle DATE was mapped to PostgreSQL `date`."""
    oracle_rows = [{"filing_id": 1, "filed_date": "2019-04-02 14:32:07"}]
    postgres_rows = [{"filing_id": 1, "filed_date": "2019-04-02 00:00:00"}]

    defects = compare_spot_check("ucc_filing", oracle_rows, postgres_rows, "filing_id")

    assert len(defects) == 1
    assert "time component was dropped" in defects[0].detail
    assert "timestamp(0)" in defects[0].detail


def test_spot_check_catches_null_becoming_empty_string():
    oracle_rows = [{"debtor_id": 7, "mailing_address_2": None}]
    postgres_rows = [{"debtor_id": 7, "mailing_address_2": ""}]
    defects = compare_spot_check("ucc_debtor", oracle_rows, postgres_rows, "debtor_id")
    assert "did not set null_as" in defects[0].detail


def test_spot_check_tolerates_numeric_type_differences():
    """Decimal('125.50') from Oracle and 125.5 from PostgreSQL are the
    same value. Flagging that as a defect would bury the real ones."""
    oracle_rows = [{"filing_id": 1, "filing_fee": "125.50"}]
    postgres_rows = [{"filing_id": 1, "filing_fee": 125.5}]
    assert compare_spot_check("ucc_filing", oracle_rows, postgres_rows,
                              "filing_id") == []


def test_spot_check_reports_a_missing_row():
    defects = compare_spot_check("ucc_filing", [{"filing_id": 9}], [], "filing_id")
    assert "absent in PostgreSQL" in defects[0].detail


# ------------------------------------------------------------ summary
def test_summary_blocks_cutover_when_a_blocker_exists():
    report = TableReport("ucc_debtor")
    ok, defect = compare_row_counts("ucc_debtor", 7400, 7399)
    report.record(ok, defect)

    result = summarize([report])
    assert result["cutover_recommended"] is False
    assert result["blockers"] == 1
    assert result["checks_failed"] == 1


def test_summary_allows_cutover_when_clean():
    report = TableReport("ucc_debtor")
    report.record(*compare_row_counts("ucc_debtor", 7400, 7400))
    assert summarize([report])["cutover_recommended"] is True


def test_warnings_alone_do_not_block():
    report = TableReport("ucc_amendment")
    defects = detect_empty_string_divergence(
        "ucc_amendment", ["notes"],
        {"null_notes": 10}, {"null_notes": 10, "empty_notes": 25},
    )
    report.record(False, defects[0])
    result = summarize([report])
    assert result["blockers"] == 0
    assert result["cutover_recommended"] is True


def test_a_clean_report_on_a_corrupted_load_would_be_a_failure():
    """The meta-test. This asserts the validator's polarity is right.

    If someone 'fixes' detect_empty_string_divergence by making it lenient
    -- comparing percentages, adding a tolerance, treating empty strings
    as equivalent to NULL -- every other test here still passes and this
    one fails. That is the point.
    """
    corrupted_load = {"null_mailing_address_2": 0, "empty_mailing_address_2": 1400}
    oracle_truth = {"null_mailing_address_2": 1400}

    defects = detect_empty_string_divergence(
        "ucc_debtor", ["mailing_address_2"], oracle_truth, corrupted_load
    )
    report = TableReport("ucc_debtor")
    for defect in defects:
        report.record(False, defect)

    assert not report.clean, (
        "The validator reported a clean result on a load that converted "
        "1,400 Oracle NULLs into empty strings. A validator that misses "
        "this is worse than no validator."
    )
    assert summarize([report])["cutover_recommended"] is False
