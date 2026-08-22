"""Construct detection, and the one thing the converter must refuse.

The registry in `oracle_constructs.py` is what tells the agent which
constructs are mechanical and which are design decisions. Getting that
boundary wrong in either direction is expensive: too strict and the agent
refuses work it could do; too lenient and it confidently produces a
translation that compiles, runs, and is wrong.
"""

from __future__ import annotations

import os

import pytest

# The construct registry ships with the appsql-rewriting skill and is
# shared with plsql-conversion. Loaded by path, as an agent would.
from conftest import load_skill_script

_oracleisms = load_skill_script('appsql-rewriting', 'find_oracleisms.py')
BY_LABEL = _oracleisms.BY_LABEL
UNTRANSLATABLE = _oracleisms.UNTRANSLATABLE
find = _oracleisms.find
must_refuse = _oracleisms.must_refuse

LAB_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_DIR = os.path.join(LAB_ROOT, "app")
ORACLE_DIR = os.path.join(LAB_ROOT, "legacy-oracle")


def _labels(text: str) -> set[str]:
    return {c.label for c in find(text)}


# ------------------------------------------------------------ detection
@pytest.mark.parametrize(
    "snippet,expected",
    [
        ("WHERE ROWNUM <= 50", "ROWNUM"),
        ("WHERE f.state_code = s.state_code(+)", "OUTER_JOIN_PLUS"),
        ("CONNECT BY PRIOR a.amendment_id = a.parent_amendment_id", "CONNECT_BY"),
        ("NVL(f.page_count, 0)", "NVL"),
        ("NVL2(x, 'has', 'none')", "NVL"),
        ("DECODE(f.status, 'ACTIVE', 'Open', 'Other')", "DECODE"),
        ("WHERE f.filed_date <= SYSDATE", "SYSDATE"),
        ("SELECT SYSTIMESTAMP FROM dual", "SYSDATE"),
        ("SELECT 1 FROM dual", "DUAL"),
        ("MERGE INTO state_sos_source t", "MERGE"),
        ("TO_CHAR(f.filed_date, 'DD-MON-RR HH24:MI')", "TO_CHAR_MASK"),
        ("ADD_MONTHS(:NEW.filed_date, 60)", "ADD_MONTHS"),
        ("TRUNC(SYSDATE) - TRUNC(f.filed_date)", "TRUNC_DATE"),
        ("pkg_risk_calc.score_debtor(d.debtor_name)", "PACKAGE_CALL"),
        ("SELECT filing_id BULK COLLECT INTO v_ids", "BULK_COLLECT"),
        ("FORALL i IN 1 .. v_ids.COUNT", "FORALL"),
        ("PRAGMA AUTONOMOUS_TRANSACTION;", "AUTONOMOUS"),
        ("SET SERVEROUTPUT ON SIZE UNLIMITED", "SQLPLUS_DIRECTIVE"),
        ("WHENEVER SQLERROR EXIT FAILURE ROLLBACK", "SQLPLUS_DIRECTIVE"),
        ("SELECT ROWID FROM ucc_filing", "ROWID"),
        ("party_name VARCHAR2(240 BYTE)", "VARCHAR2"),
    ],
)
def test_each_construct_is_detected(snippet, expected):
    assert expected in _labels(snippet), f"{expected} not found in {snippet!r}"


def test_clean_postgres_sql_triggers_nothing():
    clean = "SELECT filing_number, coalesce(page_count, 0) FROM ucc_filing LIMIT 50"
    assert _labels(clean) == set()


def test_one_line_can_carry_several_constructs():
    line = "SELECT NVL(x,0), DECODE(s,'A','B','C') FROM t WHERE ROWNUM <= 10"
    assert {"NVL", "DECODE", "ROWNUM"} <= _labels(line)


# ----------------------------------------------------- refusal boundary
def test_autonomous_transaction_must_be_refused():
    """The critical negative case.

    Dropping the pragma and emitting the rest compiles, runs, and silently
    inverts the semantics: audit rows start vanishing on exactly the
    rollbacks they exist to survive. The registry must mark this
    untranslatable so the converter refuses instead of guessing.
    """
    refusals = must_refuse("PROCEDURE log_audit IS PRAGMA AUTONOMOUS_TRANSACTION; BEGIN")
    assert [c.label for c in refusals] == ["AUTONOMOUS"]
    assert "AUTONOMOUS" in UNTRANSLATABLE


def test_the_refusal_explains_the_alternatives():
    """A refusal with no path forward just gets overridden by the next
    person. The note must name the actual options."""
    note = BY_LABEL["AUTONOMOUS"].note.lower()
    assert "dblink" in note
    assert "background worker" in note
    assert "outside the transaction" in note


def test_mechanical_constructs_are_not_marked_untranslatable():
    """Marking too much untranslatable is its own failure -- the agent
    stops doing work it is perfectly capable of."""
    for label in ["ROWNUM", "NVL", "DECODE", "MERGE", "CONNECT_BY",
                  "OUTER_JOIN_PLUS", "SYSDATE", "DUAL", "BULK_COLLECT"]:
        assert BY_LABEL[label].translatable, f"{label} should be translatable"


def test_only_two_constructs_are_untranslatable():
    assert UNTRANSLATABLE == {"AUTONOMOUS", "ROWID"}


def test_ordinary_sql_needs_no_refusal():
    assert must_refuse("SELECT NVL(a,0) FROM t WHERE ROWNUM <= 5") == []


# ------------------------------------- against the real files in the lab
@pytest.mark.parametrize(
    "filename,expected",
    [
        ("filing_repository.py", {"ROWNUM", "NVL", "OUTER_JOIN_PLUS",
                                  "CONNECT_BY", "DUAL", "SYSDATE", "DECODE"}),
        ("RiskReportDao.java", {"ROWNUM", "MERGE", "DUAL", "PACKAGE_CALL",
                                "TRUNC_DATE", "SYSDATE"}),
        ("nightly_batch.sql", {"ROWNUM", "MERGE", "CONNECT_BY", "DECODE",
                               "NVL", "OUTER_JOIN_PLUS", "DUAL",
                               "SQLPLUS_DIRECTIVE", "TO_CHAR_MASK"}),
    ],
)
def test_the_planted_app_files_contain_what_they_claim(filename, expected):
    """The lab's own fixtures have to actually contain the constructs the
    exercise says they do -- otherwise the student chases a bug that is
    really a typo in the course material."""
    path = os.path.join(APP_DIR, filename)
    assert os.path.exists(path), f"missing lab fixture: {path}"
    with open(path, encoding="utf-8") as fh:
        found = _labels(fh.read())
    missing = expected - found
    assert not missing, f"{filename} is missing planted constructs: {sorted(missing)}"


def test_the_legacy_package_contains_the_autonomous_transaction():
    """If this fails, the whole refusal exercise is unreachable."""
    path = os.path.join(ORACLE_DIR, "03_packages.sql")
    assert os.path.exists(path)
    with open(path, encoding="utf-8") as fh:
        content = fh.read()
    assert must_refuse(content), "03_packages.sql no longer plants an untranslatable construct"
