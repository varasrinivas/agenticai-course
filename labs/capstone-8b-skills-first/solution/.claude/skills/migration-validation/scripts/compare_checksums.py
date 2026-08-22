"""Reconcile a table across the two engines and emit the defect list.

Deliberately does NOT compute a pass percentage. A percentage is the mechanism
by which a broken load reaches production: "142/148 (96%)" reads as success,
and the six failures are the entire content of the report.

Severity is a judgement this script makes mechanically, from one question:
did the migration cause it?

    BLOCKER  the migration caused it            -> cutover must not proceed
    WARNING  present in the Oracle source too   -> real, but not a migration bug

That distinction matters in both directions. Reporting source drift as a
BLOCKER trains people to skip the validator, which costs more than the drift.

Run it:

    python compare_checksums.py --oracle expected.json --postgres actual.json
    python compare_checksums.py --summary artifacts/validation_summary.json
    python compare_checksums.py --self-test

Exit code is 1 if any BLOCKER is present, so it can gate the cutover.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, asdict, field

BLOCKER = "BLOCKER"
WARNING = "WARNING"


@dataclass
class Defect:
    severity: str
    check: str
    table: str
    column: str | None
    observed: object
    expected: object
    consequence: str

    def render(self) -> str:
        target = f"{self.table}.{self.column}" if self.column else self.table
        return (f"  [{self.severity}] {self.check} -- {target}\n"
                f"      observed: {self.observed}\n"
                f"      expected: {self.expected}\n"
                f"      -> {self.consequence}")


@dataclass
class TableReport:
    table: str
    oracle_rows: int
    pg_rows: int
    checks_passed: int = 0
    checks_failed: int = 0
    defects: list[Defect] = field(default_factory=list)

    def record(self, ok: bool, defect: Defect | None = None) -> None:
        if ok:
            self.checks_passed += 1
            return
        self.checks_failed += 1
        if defect is not None:
            self.defects.append(defect)


def reconcile(table: str, oracle: dict, postgres: dict,
              source_drift: set[str] | None = None) -> TableReport:
    """Run the aggregate checks for one table.

    `source_drift` names checks already known to be wrong in Oracle. Those
    downgrade to WARNING instead of BLOCKER -- the migration did not cause
    them, and mislabelling them teaches people to ignore the report.
    """
    drift = source_drift or set()
    oracle_rows = int(oracle.get("row_count", 0))
    pg_rows = int(postgres.get("row_count", 0))
    report = TableReport(table=table, oracle_rows=oracle_rows, pg_rows=pg_rows)

    # 1. row count
    report.record(
        oracle_rows == pg_rows,
        Defect(BLOCKER, "row_count", table, None, pg_rows, oracle_rows,
               f"{abs(oracle_rows - pg_rows)} rows unaccounted for; every "
               f"downstream aggregate is wrong by that much."),
    )

    # 2. fingerprint, when both sides computed one the same way
    if "fingerprint" in oracle and "fingerprint" in postgres:
        report.record(
            oracle["fingerprint"] == postgres["fingerprint"],
            Defect(BLOCKER, "checksum", table, None,
                   postgres["fingerprint"], oracle["fingerprint"],
                   "Values diverge. Note that a checksum agrees with itself "
                   "after a uniform truncation -- check the spot-check diff "
                   "before concluding this is the only damage."),
        )

    # 3 + 4. NULL and empty-string counts, per column
    for key, expected_nulls in sorted(oracle.items()):
        if not key.startswith("null_"):
            continue
        column = key[len("null_"):]
        expected_nulls = int(expected_nulls)
        actual_nulls = int(postgres.get(key, 0))
        empties = int(postgres.get(f"empty_{column}", 0))

        report.record(
            actual_nulls == expected_nulls,
            Defect(
                WARNING if f"null_{column}" in drift else BLOCKER,
                "null_count", table, column, actual_nulls, expected_nulls,
                f"{abs(expected_nulls - actual_nulls)} values changed "
                f"nullability; IS NULL predicates on this column now match a "
                f"different set of rows.",
            ),
        )

        # Oracle cannot hold an empty string, so any is manufactured.
        report.record(
            empties == 0,
            Defect(BLOCKER, "empty_string_divergence", table, column, empties, 0,
                   f"{empties} empty strings where Oracle had NULL. Oracle has "
                   f"no empty string, so the load created these. Every IS NULL "
                   f"query against this column now returns fewer rows. "
                   f"Re-load with null_as set."),
        )

    return report


def _equivalent(a, b) -> bool:
    if a == b:
        return True
    # Numeric types differ across drivers (Decimal vs float vs int).
    try:
        return float(a) == float(b)
    except (TypeError, ValueError):
        return False


def looks_truncated_to_midnight(src, tgt) -> bool:
    """Did an Oracle DATE lose its time component on the way across?

    The signature of `DATE` mapped to `date` instead of `timestamp(0)`:
    same calendar day, time zeroed, and the source actually carried a time.

    Equal values are never truncation. `compare_spot_check` only reaches here
    for values that already differ, so that guard is unreachable from there --
    but the helper is also read and called on its own, and a predicate that
    answers "yes, truncated" about two identical midnight timestamps is simply
    wrong.
    """
    src_text, tgt_text = str(src), str(tgt)
    if src_text == tgt_text:
        return False
    if "00:00:00" not in tgt_text:
        return False
    return src_text[:10] == tgt_text[:10] and src_text[:10] != src_text


def compare_spot_check(table: str, oracle_rows: list[dict],
                       postgres_rows: list[dict], key: str) -> list[Defect]:
    """Check 6 -- field-by-field diff of matched rows.

    The only check that catches DATE truncation. If `filed_date` reads
    `2019-04-02 14:32:07` in Oracle and `2019-04-02 00:00:00` in PostgreSQL,
    the row counts match, the NULL counts match, and the checksum agrees with
    itself because it was computed over the already-truncated values. Only a
    value-level comparison ever notices.
    """
    defects: list[Defect] = []
    pg_by_key = {str(r.get(key)): r for r in postgres_rows}

    for src in oracle_rows:
        identifier = str(src.get(key))
        tgt = pg_by_key.get(identifier)
        if tgt is None:
            defects.append(Defect(
                BLOCKER, "spot_check", table, None, "absent", "present",
                f"Row {key}={identifier} is in Oracle and not in PostgreSQL. "
                f"The row count matched, so this is a swap, not a shortfall.",
            ))
            continue

        for column, src_value in src.items():
            if column not in tgt:
                continue
            tgt_value = tgt[column]
            if _equivalent(src_value, tgt_value):
                continue

            hint = ""
            if looks_truncated_to_midnight(src_value, tgt_value):
                hint = (" Oracle DATE was mapped to PostgreSQL `date` instead "
                        "of `timestamp(0)` -- the time component was dropped "
                        "from every row, and no aggregate check can see it.")
            if src_value is None and tgt_value == "":
                hint = (" Oracle NULL became a PostgreSQL empty string -- the "
                        "load did not set null_as.")

            defects.append(Defect(
                BLOCKER, "spot_check", table, column, tgt_value, src_value,
                f"Row {key}={identifier} differs.{hint}",
            ))
    return defects


def render(reports: list[TableReport]) -> str:
    defects = [d for r in reports for d in r.defects]
    blockers = [d for d in defects if d.severity == BLOCKER]
    out: list[str] = []

    if defects:
        out.append(f"DEFECTS ({len(defects)})")
        out.append("-" * 71)
        out.extend(d.render() for d in defects)
        out.append("")

    out.append("PER-TABLE RECONCILIATION")
    out.append("-" * 71)
    out.append(f"{'TABLE':<22}{'ORACLE':>9}{'PG':>9}{'PASS':>7}{'FAIL':>7}")
    for r in reports:
        out.append(f"{r.table:<22}{r.oracle_rows:>9,}{r.pg_rows:>9,}"
                   f"{r.checks_passed:>7}{r.checks_failed:>7}")
    out.append("")
    out.append(f"Blockers: {len(blockers)}    Warnings: {len(defects) - len(blockers)}")
    if blockers:
        out.append("Cutover must not proceed while a blocker is open.")
    return "\n".join(out)


def to_summary(reports: list[TableReport]) -> dict:
    return {
        "tables_validated": len(reports),
        "checks_passed": sum(r.checks_passed for r in reports),
        "checks_failed": sum(r.checks_failed for r in reports),
        "defects": [asdict(d) for r in reports for d in r.defects],
    }


def _self_test() -> int:
    failures = 0

    # The planted defect: NULLs became empty strings.
    oracle = {"row_count": 7418, "null_mailing_address_2": 1412, "null_city": 0}
    broken = {"row_count": 7418, "null_mailing_address_2": 0,
              "empty_mailing_address_2": 1412, "null_city": 0}
    report = reconcile("ucc_debtor", oracle, broken)
    checks = [d.check for d in report.defects]
    if "empty_string_divergence" not in checks:
        failures += 1
        print(f"FAIL empty-string trap not detected: {checks}")
    if "null_count" not in checks:
        failures += 1
        print(f"FAIL null divergence not detected: {checks}")

    # A correct load produces no defects at all.
    good = {"row_count": 7418, "null_mailing_address_2": 1412,
            "empty_mailing_address_2": 0, "null_city": 0}
    clean = reconcile("ucc_debtor", oracle, good)
    if clean.defects:
        failures += 1
        print(f"FAIL clean load reported {len(clean.defects)} defects")
    if clean.checks_failed:
        failures += 1
        print(f"FAIL clean load counted {clean.checks_failed} failures")

    # Row-count divergence is always a blocker.
    short = reconcile("ucc_filing", {"row_count": 5000}, {"row_count": 4999})
    if not any(d.check == "row_count" and d.severity == BLOCKER for d in short.defects):
        failures += 1
        print("FAIL row-count divergence not a blocker")

    # Known source drift downgrades to WARNING rather than BLOCKER.
    drifted = reconcile("ucc_filing", {"row_count": 10, "null_status": 3},
                        {"row_count": 10, "null_status": 1, "empty_status": 0},
                        source_drift={"null_status"})
    if not any(d.severity == WARNING for d in drifted.defects):
        failures += 1
        print("FAIL source drift not downgraded to WARNING")

    # Check 6: the DATE truncation only a value-level diff can see.
    truncated = compare_spot_check(
        "ucc_filing",
        [{"filing_id": 1, "filed_date": "2019-04-02 14:32:07"}],
        [{"filing_id": 1, "filed_date": "2019-04-02 00:00:00"}],
        key="filing_id",
    )
    if not truncated:
        failures += 1
        print("FAIL DATE truncation not detected by spot check")
    elif "timestamp(0)" not in truncated[0].consequence:
        failures += 1
        print(f"FAIL truncation detected but not diagnosed: "
              f"{truncated[0].consequence}")

    # An identical row must not produce a defect.
    same = compare_spot_check(
        "ucc_filing",
        [{"filing_id": 1, "filed_date": "2019-04-02 14:32:07"}],
        [{"filing_id": 1, "filed_date": "2019-04-02 14:32:07"}],
        key="filing_id",
    )
    if same:
        failures += 1
        print(f"FAIL identical rows reported {len(same)} defects")

    # A missing row is a blocker even when counts happen to match.
    missing = compare_spot_check(
        "ucc_filing", [{"filing_id": 9}], [{"filing_id": 8}], key="filing_id")
    if not any(d.severity == BLOCKER for d in missing):
        failures += 1
        print("FAIL missing row not a blocker")

    # The report must never contain a percentage.
    text = render([report])
    if "%" in text:
        failures += 1
        print("FAIL report contains a percentage")

    print(f"{'PASS' if not failures else 'FAIL'} -- {failures} problems")
    return 1 if failures else 0


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Reconcile a migrated table.")
    parser.add_argument("--oracle", help="Oracle-side profile JSON")
    parser.add_argument("--postgres", help="PostgreSQL-side profile JSON")
    parser.add_argument("--table", default=None)
    parser.add_argument("--summary", help="also write validation_summary.json here")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    if args.self_test:
        return _self_test()

    if not (args.oracle and args.postgres):
        parser.print_help()
        return 2

    try:
        with open(args.oracle, encoding="utf-8") as handle:
            oracle = json.load(handle)
        with open(args.postgres, encoding="utf-8") as handle:
            postgres = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"cannot read profiles: {exc}", file=sys.stderr)
        return 2

    table = args.table or oracle.get("table_name", "?").lower()
    reports = [reconcile(table, oracle, postgres)]
    print(render(reports))

    if args.summary:
        with open(args.summary, "w", encoding="utf-8") as handle:
            json.dump(to_summary(reports), handle, indent=2)
        print(f"\nWrote {args.summary}")

    blockers = [d for r in reports for d in r.defects if d.severity == BLOCKER]
    return 1 if blockers else 0


if __name__ == "__main__":
    sys.exit(main())
