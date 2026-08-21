"""Reconciliation logic, as pure functions.

The validator subagent decides *what* to check and how to describe it. The
arithmetic of comparing two checksum payloads is not a judgement call, so
it lives here where it can be unit-tested exhaustively and cannot vary
between runs.

The important asymmetry: Oracle cannot report an empty-string count,
because Oracle has no empty string -- it stores `''` as NULL. So the check
that catches the headline bug in this capstone is one-sided by nature.
You compare Oracle's NULL count against PostgreSQL's NULL count, and
separately assert PostgreSQL's empty-string count is zero on any column
that had NULLs on the Oracle side.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Severity(str, Enum):
    BLOCKER = "blocker"     # do not cut over
    WARNING = "warning"     # investigate, may be acceptable
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
    """Exact equality. No tolerance, no percentage."""
    if oracle == postgres:
        return True, None
    delta = postgres - oracle
    return False, Defect(
        check="row_count",
        object=table,
        detail=(
            f"Oracle has {oracle:,} rows, PostgreSQL has {postgres:,} "
            f"({delta:+,}). A migration is not 'nearly' correct."
        ),
    )


def compare_null_counts(
    table: str, columns: list[str], oracle: dict, postgres: dict
) -> list[tuple[bool, Defect | None]]:
    """Per-column NULL counts must match exactly between source and target.

    Payload keys follow what the checksum tools return: `null_<column>`.
    """
    results = []
    for column in columns:
        key = f"null_{column.lower()}"
        src = oracle.get(key)
        tgt = postgres.get(key)

        if src is None or tgt is None:
            results.append(
                (False, Defect(
                    check="null_count",
                    object=f"{table}.{column}",
                    detail=f"Missing NULL count on "
                           f"{'Oracle' if src is None else 'PostgreSQL'} side; "
                           f"the check did not actually run.",
                    severity=Severity.WARNING,
                ))
            )
            continue

        if int(src) == int(tgt):
            results.append((True, None))
        else:
            results.append(
                (False, Defect(
                    check="null_count",
                    object=f"{table}.{column}",
                    detail=f"Oracle reports {int(src):,} NULLs, PostgreSQL "
                           f"reports {int(tgt):,}.",
                ))
            )
    return results


def detect_empty_string_divergence(
    table: str, columns: list[str], oracle: dict, postgres: dict
) -> list[Defect]:
    """THE check this capstone exists for.

    Oracle stores `''` as NULL. PostgreSQL stores it as a zero-length
    string. If a column had NULLs in Oracle and now has empty strings in
    PostgreSQL, those Oracle NULLs were converted on the way across --
    and every `IS NULL` predicate downstream silently stops matching them.

    Nothing errors. No constraint fires. The numbers just get quietly
    wrong, and stay wrong until someone reconciles a report by hand.
    """
    defects: list[Defect] = []
    for column in columns:
        empties = int(postgres.get(f"empty_{column.lower()}", 0) or 0)
        if empties == 0:
            continue

        oracle_nulls = int(oracle.get(f"null_{column.lower()}", 0) or 0)
        pg_nulls = int(postgres.get(f"null_{column.lower()}", 0) or 0)

        if oracle_nulls > 0 and pg_nulls < oracle_nulls:
            defects.append(
                Defect(
                    check="empty_string_divergence",
                    object=f"{table}.{column}",
                    detail=(
                        f"{empties:,} empty strings in PostgreSQL. Oracle "
                        f"reported {oracle_nulls:,} NULLs here; PostgreSQL "
                        f"reports only {pg_nulls:,}. "
                        f"{oracle_nulls - pg_nulls:,} Oracle NULLs were "
                        f"converted to empty strings by the load. Every "
                        f"IS NULL query against this column now returns "
                        f"fewer rows than it did. Re-load with null_as set."
                    ),
                    severity=Severity.BLOCKER,
                )
            )
        else:
            defects.append(
                Defect(
                    check="empty_string_present",
                    object=f"{table}.{column}",
                    detail=(
                        f"{empties:,} empty strings in PostgreSQL, but the "
                        f"Oracle NULL count ({oracle_nulls:,}) is consistent "
                        f"with the PostgreSQL NULL count ({pg_nulls:,}). "
                        f"Probably genuine empty strings rather than "
                        f"converted NULLs -- confirm before dismissing."
                    ),
                    severity=Severity.WARNING,
                )
            )
    return defects


def compare_spot_check(table: str, oracle_rows: list[dict],
                       postgres_rows: list[dict], key: str) -> list[Defect]:
    """Field-by-field diff of matched rows.

    This is what catches DATE truncation. If `filed_date` reads
    `2019-04-02 14:32:07` in Oracle and `2019-04-02 00:00:00` in
    PostgreSQL, the row counts match, the NULL counts match, and only a
    value-level comparison ever notices.
    """
    defects: list[Defect] = []
    pg_by_key = {str(r.get(key)): r for r in postgres_rows}

    for src in oracle_rows:
        identifier = str(src.get(key))
        tgt = pg_by_key.get(identifier)
        if tgt is None:
            defects.append(
                Defect("spot_check", f"{table}[{key}={identifier}]",
                       "Row present in Oracle, absent in PostgreSQL.")
            )
            continue

        for column, src_value in src.items():
            if column not in tgt:
                continue
            tgt_value = tgt[column]
            if _equivalent(src_value, tgt_value):
                continue

            hint = ""
            if _looks_truncated_to_midnight(src_value, tgt_value):
                hint = (" This is Oracle DATE mapped to PostgreSQL `date` "
                        "instead of `timestamp(0)` -- the time component was "
                        "dropped.")
            if src_value is None and tgt_value == "":
                hint = (" Oracle NULL became a PostgreSQL empty string -- "
                        "the load did not set null_as.")

            defects.append(
                Defect("spot_check", f"{table}.{column}[{key}={identifier}]",
                       f"Oracle={src_value!r} PostgreSQL={tgt_value!r}.{hint}")
            )
    return defects


def _equivalent(a, b) -> bool:
    if a == b:
        return True
    # Numeric types differ across drivers (Decimal vs float vs int).
    try:
        return float(a) == float(b)
    except (TypeError, ValueError):
        return False


def _looks_truncated_to_midnight(src, tgt) -> bool:
    src_text, tgt_text = str(src), str(tgt)
    if "00:00:00" not in tgt_text:
        return False
    return src_text[:10] == tgt_text[:10] and src_text[:10] != src_text


def summarize(reports: list[TableReport]) -> dict:
    """The JSON the validator writes and the report page reads.

    Defects come first and are never collapsed into a percentage. "94% of
    checks passed" is not an acceptable way to describe a data-corruption
    bug.
    """
    all_defects = [d for r in reports for d in r.defects]
    return {
        "tables_validated": len(reports),
        "checks_passed": sum(r.checks_passed for r in reports),
        "checks_failed": sum(r.checks_failed for r in reports),
        "blockers": sum(1 for d in all_defects if d.severity is Severity.BLOCKER),
        "defects": [d.to_dict() for d in all_defects],
        "cutover_recommended": not any(
            d.severity is Severity.BLOCKER for d in all_defects
        ),
    }
