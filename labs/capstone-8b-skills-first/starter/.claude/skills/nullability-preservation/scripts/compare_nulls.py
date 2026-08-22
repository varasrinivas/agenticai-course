"""Prove that NULL survived the Oracle -> PostgreSQL crossing.

The check this script performs is the one a row count cannot do.

Read SKILL.md TODO(4) first -- it is where you write the rule, and this file
implements exactly that rule. If you write the code first you will end up with
a rule that describes your code rather than the other way round, and the
loading phase reads the rule, not the code.

    python compare_nulls.py --table ucc_debtor --column mailing_address_2 \\
        --oracle-nulls 1412 --pg-nulls 0 --pg-empty 1412
    python compare_nulls.py --profile expected.json --observed actual.json
    python compare_nulls.py --self-test

Exit code must be non-zero when a defect is found, so this can gate a
pipeline. A checker that always exits 0 is decoration.
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
        # TODO(1): the rule, in one expression.
        #
        # Two conditions, and the second is the one people leave out. Think
        # about what Oracle is capable of storing before deciding whether a
        # non-zero empty-string count can ever be legitimate.
        raise NotImplementedError("is_defect: see TODO(1)")

    @property
    def diagnosis(self) -> str:
        """TODO(2): say WHICH failure this is, not just that it failed.

        There are several distinct ways this check fails and they have
        different fixes:
          - NULLs became empty strings (the planted defect)
          - empty strings appeared with NULL counts unchanged
          - more NULLs than Oracle had (values dropped entirely)
          - fewer NULLs with no empty strings to account for them

        A reader who gets "mismatch" learns nothing. Name the failure.
        """
        raise NotImplementedError("diagnosis: see TODO(2)")

    def render(self) -> str:
        # TODO(3): the three counts, aligned, plus the diagnosis when it is a
        # defect. Align the numbers -- a reader scanning six tables needs the
        # odd one out to jump.
        raise NotImplementedError("render: see TODO(3)")


@dataclass
class Report:
    verdicts: list[ColumnVerdict] = field(default_factory=list)

    @property
    def defects(self) -> list[ColumnVerdict]:
        return [v for v in self.verdicts if v.is_defect]

    def render(self) -> str:
        # TODO(4): defects FIRST, then the summary.
        #
        # Do not emit a percentage. Work out why before you write this --
        # SKILL.md TODO(5) is the same question, and your answer should be the
        # same in both places.
        raise NotImplementedError("Report.render: see TODO(4)")


def compare_profiles(expected: dict, observed: dict, table: str) -> Report:
    """Compare an Oracle-side profile against a PostgreSQL-side one.

    TODO(5): the fixtures use `null_<column>` keys; you will need an
    `empty_<column>` convention for the PostgreSQL side.

    Decide what to do about a column present in `expected` but missing from
    `observed`. There are two defensible answers and one indefensible one --
    do not let a missing measurement read as a passing one.
    """
    raise NotImplementedError("compare_profiles: see TODO(5)")


def _self_test() -> int:
    """TODO(6): cases.

    Cover at minimum: the planted defect, a correct load, partial damage,
    empty strings with matching NULL counts, and values lost outright.

    Add one assertion that every defect carries a non-empty diagnosis. A
    defect nobody can act on has not really been reported.
    """
    print("TODO(6): no self-test cases yet")
    return 1


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

    # TODO(7): wire both modes through, and return 1 when a defect is found.
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
