"""The Oracle -> PostgreSQL type mapping, as code, bundled with the skill.

Why this is a script and not a paragraph in SKILL.md: a mapping table written
only in prose cannot be unit-tested, cannot be diffed when someone changes it,
and produces a different answer on a bad day. Encoding the mechanical part
here means the model spends its judgement on the cases that actually need it.

Build this before writing the traps section of SKILL.md -- running it over
`legacy-oracle/01_schema.sql` is how you find which columns are traps.

    python check_mapping.py --type "NUMBER(9)"
    python check_mapping.py --ddl ../../../../legacy-oracle/01_schema.sql
    python check_mapping.py --self-test

`tests/test_type_mapping.py` imports `map_type`, `Confidence` and
`quote_policy` from this file by path. Keep those names.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from enum import Enum


class Confidence(str, Enum):
    CONFIDENT = "confident"     # mechanical, no judgement needed
    CHECK_DATA = "check_data"   # correct answer depends on the values
    MANUAL = "manual"           # no good equivalent; a human decides


@dataclass(frozen=True)
class Mapping:
    oracle_type: str
    postgres_type: str
    reason: str
    confidence: Confidence = Confidence.CONFIDENT

    @property
    def needs_review(self) -> bool:
        return self.confidence is not Confidence.CONFIDENT


# TODO(1): Regexes for the parameterised types. NUMBER is the fiddly one --
# it has to match `NUMBER`, `NUMBER(12)`, `NUMBER(9,2)`, `NUMBER(*)`, and
# `NUMBER(9,-2)` (negative scale is legal and rounds LEFT of the decimal
# point).
_NUMBER = None
_VARCHAR2 = None
_CHAR = None
_RAW = None
_TIMESTAMP = None


def map_type(oracle_type: str, *, sample_values: list | None = None) -> Mapping:
    """Map one Oracle column type to PostgreSQL.

    `sample_values` is optional but changes the answer for at least one type.
    Work out which one, and why the DDL alone cannot settle it.
    """
    declared = (oracle_type or "").strip()
    upper = declared.upper()

    # TODO(2): NUMBER precision/scale rules.
    #   no precision  -> ?, and at what confidence? (it may carry a scale)
    #   scale > 0     -> ?
    #   scale < 0     -> ?  (no PostgreSQL equivalent -- what does that imply?)
    #   p <= 4 / <= 9 / <= 18 / otherwise -> ?

    # TODO(3): VARCHAR2(n BYTE) and VARCHAR2(n CHAR). Both become varchar(n),
    # but only one of them is a clean equivalence. The other depends on
    # whether the data is ASCII, so it cannot be CONFIDENT.

    # TODO(4): THE most consequential row in this table.
    #
    #   DATE -> ?
    #
    # Oracle DATE carries a time component. The obvious mapping compiles,
    # loads, and silently truncates 14:32:07 to midnight -- which changes
    # which filings appear to have lapsed. Nothing errors. Put the reason in
    # the Mapping so the decision log explains itself.

    # TODO(5): TIMESTAMP, with and without time zone. WITH LOCAL TIME ZONE is
    # the one with no exact equivalent -- Oracle renders it in the session's
    # zone, PostgreSQL in the client's. Decide the confidence accordingly.

    # TODO(6): RAW(n). The n == 16 case is not decidable from the DDL alone;
    # this is what `sample_values` is for.

    # TODO(7): the simple direct equivalents -- CLOB, NCLOB, BLOB, BFILE,
    # LONG, BINARY_FLOAT, BINARY_DOUBLE, FLOAT, ROWID, UROWID, XMLTYPE.
    # Three of these should be MANUAL rather than CONFIDENT. Work out which.

    # TODO(8): the fallback. An unrecognised type has to return something --
    # but make the reason say clearly that it is a placeholder and not an
    # answer, or it will be read as one.
    raise NotImplementedError("map_type: see TODO(2) through TODO(8)")


def quote_policy(identifier: str) -> str:
    """Oracle folds unquoted identifiers to upper; PostgreSQL folds to lower.

    TODO(9): decide what the migration does, and implement it. Whatever you
    choose, every hand-written query afterwards lives with it -- so write the
    reasoning in the docstring, not just the code.
    """
    raise NotImplementedError("quote_policy: see TODO(9)")


# ---------------------------------------------------------------- CLI
def columns_from_ddl(ddl: str) -> list[tuple[str, str]]:
    """Pull (column_name, declared_type) pairs out of a CREATE TABLE body.

    TODO(10): a forgiving regex, not a SQL parser. Anything it misses gets
    mapped by hand, which is the safe direction to fail. Skip the lines that
    are constraints rather than columns.
    """
    raise NotImplementedError("columns_from_ddl: see TODO(10)")


def _self_test() -> int:
    """TODO(11): the cases that have actually gone wrong on real migrations.

    At minimum cover: each NUMBER precision band, NUMBER with a scale, bare
    NUMBER, DATE, TIMESTAMP WITH LOCAL TIME ZONE, RAW(16) vs RAW(32), and one
    type that must come back MANUAL.

    Assert the confidence as well as the target type. A mapping that is right
    for the wrong reason will drift.
    """
    print("TODO(11): no self-test cases yet")
    return 1


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Map Oracle column types to PostgreSQL 16, with a confidence.")
    parser.add_argument("--type", help="a single Oracle type, e.g. 'NUMBER(9)'")
    parser.add_argument("--ddl", help="path to a file containing Oracle CREATE TABLE DDL")
    parser.add_argument("--sample", nargs="*", default=None,
                        help="sample values; changes the answer for one type")
    parser.add_argument("--self-test", action="store_true", help="run the built-in cases")
    args = parser.parse_args(argv)

    if args.self_test:
        return _self_test()

    # TODO(12): wire --type and --ddl through to map_type/columns_from_ddl and
    # print a result that makes the confidence impossible to miss. The agent
    # reads this output to decide where to spend its attention, so a flat list
    # where `confident` and `manual` look alike defeats the point.
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
