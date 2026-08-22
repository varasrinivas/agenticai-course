"""The registry of Oracle constructs that do not survive a move to PostgreSQL.

Bundled with the skill rather than sitting at the project root, because the
knowledge and the code that detects it ought to move together.

TWO skills import this file: `appsql-rewriting` scans application source with
it, and `plsql-conversion` uses it to decide whether an object must be
refused. One catalog, two consumers, so they cannot disagree about what counts
as an Oracle-ism. Keep it dependency-free -- no SDK, no config import -- so it
runs anywhere and unit-tests in milliseconds.

    python find_oracleisms.py --dir ../app
    python find_oracleisms.py --dir ../legacy-oracle --refuse-only
    python find_oracleisms.py --self-test

`tests/test_plsql_conversion.py` imports `BY_LABEL`, `UNTRANSLATABLE`, `find`
and `must_refuse` from this file by path. Keep those names.
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class Construct:
    label: str
    pattern: re.Pattern
    note: str
    translatable: bool = True

    def found_in(self, text: str) -> bool:
        return bool(self.pattern.search(text))


# TODO(1): build the registry.
#
# Read `app/filing_repository.py`, `app/RiskReportDao.java`,
# `app/nightly_batch.sql` and `legacy-oracle/03_packages.sql`, and add a
# Construct for every Oracle-specific thing you find. Roughly 19 of them.
#
# Each needs a stable label, a case-insensitive regex, and a note saying what
# it becomes AND what the trap is. The note is what the agent reads at the
# moment it decides on a rewrite, so "-> LIMIT" is not enough.
#
# TODO(2): set translatable=False on the ones with no correct mechanical
# translation. There are exactly two. Getting this set right is the whole
# safety property of the PL/SQL converter -- a construct wrongly marked
# translatable produces a confident wrong conversion that passes review.
#
# One of them is a pragma whose entire purpose is to survive a rollback.
# The other maps to something that is not stable across VACUUM.
CONSTRUCTS: list[Construct] = []

BY_LABEL = {c.label: c for c in CONSTRUCTS}
UNTRANSLATABLE = {c.label for c in CONSTRUCTS if not c.translatable}

SOURCE_SUFFIXES = (".py", ".java", ".sql", ".xml", ".jsp", ".properties")


def find(text: str) -> list[Construct]:
    """Every construct present in a chunk of SQL or source."""
    # TODO(3)
    raise NotImplementedError("find: see TODO(3)")


def must_refuse(text: str) -> list[Construct]:
    """Constructs that have no safe translation.

    A non-empty result means the correct output is a refusal with an
    explanation, not a conversion.

    TODO(4): implement, then write the docstring line that explains why a
    confident wrong translation is worse than no translation at all.
    """
    raise NotImplementedError("must_refuse: see TODO(4)")


def scan_text(text: str, path: str = "<text>") -> list[dict]:
    """Locate every construct occurrence, with line numbers.

    TODO(5): line-level, not file-level. The deliverable is a diff, and a diff
    needs to point at a line. Return dicts carrying at least: path, line,
    construct, translatable, note, and the source line itself.
    """
    raise NotImplementedError("scan_text: see TODO(5)")


def scan_file(path: str) -> list[dict]:
    # TODO(6): read the file and delegate to scan_text. Do not let one
    # unreadable file abort a directory scan.
    raise NotImplementedError("scan_file: see TODO(6)")


def scan_dir(root: str) -> list[dict]:
    # TODO(7): walk the tree, skipping __pycache__, .git and build output.
    raise NotImplementedError("scan_dir: see TODO(7)")


def _report(hits: list[dict]) -> int:
    """TODO(8): human-readable output, grouped by file.

    Mark the untranslatable hits so they cannot be skimmed past, and end with
    a count. If any are present, say plainly that the correct output for those
    is a MANUAL_REVIEW.md rather than a conversion.
    """
    raise NotImplementedError("_report: see TODO(8)")


def _self_test() -> int:
    """TODO(9): one case per construct, asserting both that it is detected and
    that its `translatable` flag is what you intended.

    Add one assertion on the whole UNTRANSLATABLE set. If someone later flips
    a flag, that assertion is what catches it -- a per-construct test will not,
    because it will have been updated to match.
    """
    print("TODO(9): no self-test cases yet")
    return 1


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Find Oracle-specific constructs in application source.")
    parser.add_argument("--dir", help="directory to scan recursively")
    parser.add_argument("--file", help="single file to scan")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument("--refuse-only", action="store_true",
                        help="report only constructs with no safe translation")
    parser.add_argument("--self-test", action="store_true", help="run the built-in cases")
    args = parser.parse_args(argv)

    if args.self_test:
        return _self_test()

    # TODO(10): wire --file / --dir / --json / --refuse-only through.
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
