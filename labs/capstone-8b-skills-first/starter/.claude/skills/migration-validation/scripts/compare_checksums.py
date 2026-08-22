"""Reconcile a table across the two engines and emit the defect list.

Implements checks 1-2, 3-4 and 6 from `references/check-catalog.md`.

    python compare_checksums.py --oracle expected.json --postgres actual.json
    python compare_checksums.py --self-test

Exit code must be non-zero when a BLOCKER is present, so this can gate the
cutover.

`tests/test_validator_catches_empty_string.py` imports `BLOCKER`, `WARNING`,
`reconcile`, `render`, `to_summary`, `compare_spot_check` and
`looks_truncated_to_midnight` from this file by path. Keep those names.
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
        # TODO(1): severity, check, target, both values, and the consequence.
        # The consequence line is what makes someone act. "counts differ" is
        # not a consequence; "every IS NULL query on this column now returns
        # fewer rows" is.
        raise NotImplementedError("Defect.render: see TODO(1)")


@dataclass
class TableReport:
    table: str
    oracle_rows: int
    pg_rows: int
    checks_passed: int = 0
    checks_failed: int = 0
    defects: list[Defect] = field(default_factory=list)

    def record(self, ok: bool, defect: Defect | None = None) -> None:
        # TODO(2): count the check either way, and keep the defect when it
        # failed. Both counters matter -- checks_passed with no
        # checks_failed is how you tell "clean" from "never ran".
        raise NotImplementedError("record: see TODO(2)")


def reconcile(table: str, oracle: dict, postgres: dict,
              source_drift: set[str] | None = None) -> TableReport:
    """Run the aggregate checks for one table.

    `source_drift` names checks already known to be wrong in Oracle.

    TODO(3): implement checks 1, 2, 3 and 4.

    Check 4 is the important one and it is NOT a comparison -- work out what
    shape it takes instead, and why. SKILL.md TODO(3) asks the same question.

    TODO(4): use `source_drift` to downgrade a defect from BLOCKER to WARNING.
    Then think about what happens to a team that gets BLOCKERs for problems
    the migration did not cause, and make sure your severity rule reflects it.
    """
    raise NotImplementedError("reconcile: see TODO(3) and TODO(4)")


def _equivalent(a, b) -> bool:
    # TODO(5): Decimal vs float vs int is a driver artefact, not a defect.
    # Compare accordingly, without swallowing real differences.
    raise NotImplementedError("_equivalent: see TODO(5)")


def looks_truncated_to_midnight(src, tgt) -> bool:
    """Did an Oracle DATE lose its time component on the way across?

    TODO(6): detect the signature of `DATE` mapped to `date` instead of
    `timestamp(0)`.

    Careful with the edge case where the source was already midnight -- and
    with two values that are simply equal. Neither is truncation, and a
    predicate that says otherwise is wrong even if `compare_spot_check` never
    hands it those inputs.
    """
    raise NotImplementedError("looks_truncated_to_midnight: see TODO(6)")


def compare_spot_check(table: str, oracle_rows: list[dict],
                       postgres_rows: list[dict], key: str) -> list[Defect]:
    """Check 6 -- field-by-field diff of matched rows.

    TODO(7): match rows by `key`, then compare every shared column.

    Handle three outcomes: the row is missing entirely, the values differ for
    a knowable reason (add a hint), and the values differ for an unknown one.

    Two hints are worth special-casing because they name a specific upstream
    mistake: one is the DATE truncation above, the other is a NULL that
    arrived as an empty string. Both tell the reader which earlier phase to go
    and fix.
    """
    raise NotImplementedError("compare_spot_check: see TODO(7)")


def render(reports: list[TableReport]) -> str:
    # TODO(8): defects first, then a per-table reconciliation table, then the
    # blocker/warning counts.
    #
    # No percentages. `test_report_never_emits_a_percentage` asserts it.
    raise NotImplementedError("render: see TODO(8)")


def to_summary(reports: list[TableReport]) -> dict:
    # TODO(9): the JSON the cutover gate reads. Keys: tables_validated,
    # checks_passed, checks_failed, defects[]. It must be serialisable as-is.
    raise NotImplementedError("to_summary: see TODO(9)")


def _self_test() -> int:
    """TODO(10): cases.

    Cover the planted defect, a clean load producing zero defects, a
    row-count shortfall, source drift downgrading to WARNING, DATE truncation
    caught by the spot check, and identical rows producing nothing.

    Add the assertion that the rendered report contains no '%'.
    """
    print("TODO(10): no self-test cases yet")
    return 1


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

    # TODO(11): load both profiles, reconcile, render, optionally write the
    # summary, and return 1 if any BLOCKER is present.
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
