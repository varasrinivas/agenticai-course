"""Prove that NULL survived the Oracle -> PostgreSQL crossing.

The check this script performs is the one a row count cannot do. Oracle
collapses '' into NULL; PostgreSQL does not. A load that writes zero-length
strings where Oracle had NULL produces matching row counts, matching text
checksums, and wrong data.

The rule, stated once so that both the loader and the validator read it from
the same place:

    for every column:
        oracle_nulls == pg_nulls          and     pg_empty_strings == 0

The second half is the one that matters. Oracle cannot have stored an empty
string -- it has no such value -- so any empty string on the PostgreSQL side
was manufactured by the load.

Run it:

    python compare_nulls.py --table ucc_debtor --column mailing_address_2 \\
        --oracle-nulls 1412 --pg-nulls 0 --pg-empty 1412
    python compare_nulls.py --profile expected.json --observed actual.json
    python compare_nulls.py --self-test

Exit code is 1 when a defect is found, so it can gate a pipeline.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ColumnVerdict:
    table: str
    column: str
    oracle_nulls: int
    pg_nulls: int
    pg_empty: int

    @property
    def is_defect(self) -> bool:
        return self.pg_nulls != self.oracle_nulls or self.pg_empty > 0

    @property
    def diagnosis(self) -> str:
        if not self.is_defect:
            return "ok"
        if self.pg_empty and self.pg_nulls < self.oracle_nulls:
            missing = self.oracle_nulls - self.pg_nulls
            return (f"the load wrote empty strings where Oracle had NULL "
                    f"({missing} of {self.oracle_nulls} converted to '')")
        if self.pg_empty:
            return (f"{self.pg_empty} empty strings present; Oracle cannot have "
                    f"stored an empty string, so the load manufactured them")
        if self.pg_nulls > self.oracle_nulls:
            return (f"{self.pg_nulls - self.oracle_nulls} more NULLs than Oracle -- "
                    f"values were dropped, not just retyped")
        return (f"{self.oracle_nulls - self.pg_nulls} fewer NULLs than Oracle "
                f"with no empty strings to account for them")

    def render(self) -> str:
        lines = [f"  {self.table}.{self.column}",
                 f"    Oracle NULL count:      {self.oracle_nulls:>6}",
                 f"    PostgreSQL NULL count:  {self.pg_nulls:>6}",
                 f"    PostgreSQL '' count:    {self.pg_empty:>6}"]
        if self.is_defect:
            lines.append(f"    -> {self.diagnosis}")
        return "\n".join(lines)


@dataclass
class Report:
    verdicts: list[ColumnVerdict] = field(default_factory=list)

    @property
    def defects(self) -> list[ColumnVerdict]:
        return [v for v in self.verdicts if v.is_defect]

    def render(self) -> str:
        out: list[str] = []
        defects = self.defects
        if defects:
            out.append(f"DEFECTS ({len(defects)})")
            out.extend(v.render() for v in defects)
            out.append("")
        clean = len(self.verdicts) - len(defects)
        out.append(f"{clean}/{len(self.verdicts)} columns preserved NULL correctly.")
        if defects:
            # Deliberately not a percentage. A percentage is how this gets ignored.
            out.append("A single defect here means the load is not usable. "
                       "Do not average it into a pass rate.")
        return "\n".join(out)


def compare_profiles(expected: dict, observed: dict, table: str) -> Report:
    """Compare an Oracle-side profile against a PostgreSQL-side one.

    Keys are read in the shape the fixtures use: `null_<column>` for NULL
    counts and `empty_<column>` for empty-string counts. A column present in
    `expected` but absent from `observed` is treated as zero observed NULLs,
    which reports as a defect rather than being skipped -- a missing
    measurement is not a passing one.
    """
    report = Report()
    for key, oracle_nulls in sorted(expected.items()):
        if not key.startswith("null_"):
            continue
        column = key[len("null_"):]
        report.verdicts.append(ColumnVerdict(
            table=table,
            column=column,
            oracle_nulls=int(oracle_nulls),
            pg_nulls=int(observed.get(key, 0)),
            pg_empty=int(observed.get(f"empty_{column}", 0)),
        ))
    return report


def _load(path: str) -> dict:
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def _self_test() -> int:
    cases = [
        # the planted defect: every NULL became an empty string
        (ColumnVerdict("ucc_debtor", "mailing_address_2", 1412, 0, 1412), True),
        # a correct load
        (ColumnVerdict("ucc_debtor", "mailing_address_2", 1412, 1412, 0), False),
        # partial damage -- still a defect
        (ColumnVerdict("ucc_debtor", "mailing_address_2", 1412, 1400, 12), True),
        # empty strings with matching NULL counts is still wrong: Oracle
        # cannot have held an empty string, so these were manufactured
        (ColumnVerdict("ucc_filing", "status", 0, 0, 5), True),
        # values lost outright
        (ColumnVerdict("ucc_filing", "status", 10, 25, 0), True),
        (ColumnVerdict("ucc_filing", "status", 0, 0, 0), False),
    ]
    failures = 0
    for verdict, expected_defect in cases:
        if verdict.is_defect is not expected_defect:
            failures += 1
            print(f"FAIL {verdict.table}.{verdict.column} "
                  f"({verdict.oracle_nulls}/{verdict.pg_nulls}/{verdict.pg_empty}): "
                  f"is_defect={verdict.is_defect}, expected {expected_defect}")

    # A defect must always carry a diagnosis a human can act on.
    for verdict, expected_defect in cases:
        if expected_defect and verdict.diagnosis == "ok":
            failures += 1
            print(f"FAIL {verdict.column}: defect with no diagnosis")

    print(f"{len(cases) - failures}/{len(cases)} passed")
    return 1 if failures else 0


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Verify NULL semantics survived the migration.")
    parser.add_argument("--table", default="?")
    parser.add_argument("--column")
    parser.add_argument("--oracle-nulls", type=int)
    parser.add_argument("--pg-nulls", type=int)
    parser.add_argument("--pg-empty", type=int, default=0)
    parser.add_argument("--profile", help="Oracle-side profile JSON (expected)")
    parser.add_argument("--observed", help="PostgreSQL-side profile JSON (actual)")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    if args.self_test:
        return _self_test()

    if args.profile and args.observed:
        try:
            expected, observed = _load(args.profile), _load(args.observed)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"cannot read profiles: {exc}", file=sys.stderr)
            return 2
        table = expected.get("table_name", args.table)
        report = compare_profiles(expected, observed, table)
        print(report.render())
        return 1 if report.defects else 0

    if args.column is not None and args.oracle_nulls is not None and args.pg_nulls is not None:
        verdict = ColumnVerdict(args.table, args.column, args.oracle_nulls,
                                args.pg_nulls, args.pg_empty)
        report = Report([verdict])
        print(report.render())
        return 1 if verdict.is_defect else 0

    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
