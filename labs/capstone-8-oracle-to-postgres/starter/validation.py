"""Reconciliation logic -- YOU BUILD THIS FILE.

The validator subagent decides *what* to check and how to describe it. The
arithmetic of comparing two checksum payloads is not a judgement call, so
it lives here where it can be tested exhaustively and cannot drift between
runs.

The important asymmetry to internalise before you start: Oracle cannot
report an empty-string count, because Oracle has no empty string -- it
stores `''` as NULL. So the check that catches the headline bug in this
capstone is one-sided by nature. You compare Oracle's NULL count against
PostgreSQL's NULL count, and separately assert that PostgreSQL's
empty-string count is zero on any column that had NULLs on the Oracle side.

Verify with:  pytest tests/test_validator_catches_empty_string.py -v
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Severity(str, Enum):
    BLOCKER = "blocker"     # do not cut over
    WARNING = "warning"     # investigate; may be acceptable
    INFO = "info"


@dataclass
class Defect:
    check: str
    object: str
    detail: str
    severity: Severity = Severity.BLOCKER

    def to_dict(self) -> dict:
        return {
            "check": self.check,
            "object": self.object,
            "detail": self.detail,
            "severity": self.severity.value,
        }


@dataclass
class TableReport:
    """Given complete."""

    table: str
    checks_passed: int = 0
    checks_failed: int = 0
    defects: list[Defect] = field(default_factory=list)

    def record(self, ok: bool, defect: Defect | None = None) -> None:
        if ok:
            self.checks_passed += 1
        else:
            self.checks_failed += 1
            if defect:
                self.defects.append(defect)

    @property
    def clean(self) -> bool:
        return self.checks_failed == 0


def compare_row_counts(table: str, oracle: int, postgres: int) -> tuple[bool, Defect | None]:
    """TODO(1): Exact equality. No tolerance, no percentage.

    Return (True, None) on a match. On a mismatch return a BLOCKER defect
    whose detail shows both counts and the signed delta. A migration is not
    'nearly' correct.
    """
    raise NotImplementedError("Build compare_row_counts")


def compare_null_counts(
    table: str, columns: list[str], oracle: dict, postgres: dict
) -> list[tuple[bool, Defect | None]]:
    """TODO(2): Per-column NULL counts must match exactly.

    Payload keys follow what the checksum tools return: `null_<column>`.

    Watch the missing-key case. If either side has no count for a column,
    the check did not actually run -- and that must not look like a pass.
    Report it as a WARNING that says so.
    """
    raise NotImplementedError("Build compare_null_counts")


def detect_empty_string_divergence(
    table: str, columns: list[str], oracle: dict, postgres: dict
) -> list[Defect]:
    """TODO(3): THE check this capstone exists for.

    Oracle stores `''` as NULL. PostgreSQL stores it as a zero-length
    string. If a column had NULLs in Oracle and now has empty strings in
    PostgreSQL, those Oracle NULLs were converted on the way across -- and
    every `IS NULL` predicate downstream silently stops matching them.
    Nothing errors. No constraint fires. The numbers just get quietly
    wrong and stay wrong until someone reconciles a report by hand.

    Distinguish two cases:

      - Oracle had NULLs AND PostgreSQL now has fewer NULLs than Oracle
        did -> BLOCKER. Those NULLs became empty strings. Say how many,
        and tell the reader to re-load with null_as set.

      - PostgreSQL has empty strings but the NULL counts reconcile ->
        WARNING. Probably genuine empty strings, but worth confirming
        before dismissing.

    Getting that distinction right is the difference between a validator
    people trust and one they learn to ignore.
    """
    raise NotImplementedError("Build detect_empty_string_divergence")


def compare_spot_check(table: str, oracle_rows: list[dict],
                       postgres_rows: list[dict], key: str) -> list[Defect]:
    """TODO(4): Field-by-field diff of rows matched on `key`.

    This is what catches DATE truncation. If `filed_date` reads
    `2019-04-02 14:32:07` in Oracle and `2019-04-02 00:00:00` in
    PostgreSQL, the row counts match, the NULL counts match, and only a
    value-level comparison ever notices.

    Two pieces of polish that decide whether this check is useful:

      - Tolerate numeric type differences. Decimal('125.50') from the
        Oracle driver and 125.5 from psycopg are the same value; flagging
        that would bury the real defects under noise.
      - When you spot a midnight-truncated timestamp or a NULL that became
        `''`, say WHICH bug it is in the detail. "Oracle=X PostgreSQL=Y"
        is a fact; "the DATE was mapped to `date` instead of
        `timestamp(0)`" is a fix.
    """
    raise NotImplementedError("Build compare_spot_check")


def summarize(reports: list[TableReport]) -> dict:
    """TODO(5): The JSON the validator writes and the report page reads.

    Keys: tables_validated, checks_passed, checks_failed, blockers,
    defects[], cutover_recommended.

    `cutover_recommended` is False if ANY defect is a BLOCKER. Warnings
    alone do not block.

    Do not add an overall pass percentage. "94% of checks passed" is not
    an acceptable way to describe a data-corruption bug, and the moment
    the number exists someone will lead with it.
    """
    raise NotImplementedError("Build summarize")
