"""The registry of Oracle constructs that do not survive a move to PostgreSQL.

Bundled with the skill rather than sitting at the project root, because the
knowledge ("MERGE needs a unique constraint to conflict on") and the code that
detects it ought to move together. In the subagent build of this migration the
regexes lived in `oracle_constructs.py` and the guidance lived in two different
subagent prompts, which is how the two drifted.

Two skills import this file: `appsql-rewriting` scans application source with
it, and `plsql-conversion` uses it to decide whether an object must be refused.
One catalog, two consumers, so they cannot disagree about what counts as an
Oracle-ism.

Each entry carries a `translatable` flag. `False` means there is no correct
mechanical translation and the converter must refuse rather than guess --
`PRAGMA AUTONOMOUS_TRANSACTION` being the case that matters.

Run it directly:

    python find_oracleisms.py --dir ../app
    python find_oracleisms.py --file ../app/filing_repository.py
    python find_oracleisms.py --dir ../app --json
    python find_oracleisms.py --self-test
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


CONSTRUCTS: list[Construct] = [
    Construct("ROWNUM", re.compile(r"\bROWNUM\b", re.I),
              "Oracle top-N pseudo-column -> LIMIT / OFFSET. ROWNUM is assigned "
              "before ORDER BY, which is why the Oracle form nests a subquery."),
    Construct("OUTER_JOIN_PLUS", re.compile(r"\(\s*\+\s*\)"),
              "Oracle (+) outer join operator -> LEFT/RIGHT JOIN. The (+) marks "
              "the nullable side, which is the opposite side from the one named "
              "in LEFT JOIN."),
    Construct("CONNECT_BY", re.compile(r"\bCONNECT\s+BY\b", re.I),
              "Hierarchical query -> WITH RECURSIVE. LEVEL becomes a carried "
              "counter, SYS_CONNECT_BY_PATH becomes concatenation, "
              "CONNECT_BY_ISLEAF becomes NOT EXISTS, ORDER SIBLINGS BY has no "
              "equivalent."),
    Construct("NVL", re.compile(r"\bNVL2?\s*\(", re.I),
              "NVL -> COALESCE; NVL2(a,b,c) -> CASE WHEN a IS NOT NULL THEN b "
              "ELSE c END."),
    Construct("DECODE", re.compile(r"\bDECODE\s*\(", re.I),
              "DECODE -> CASE. Note that DECODE treats NULL as matchable and "
              "CASE does not."),
    Construct("SYSDATE", re.compile(r"\bSYS(DATE|TIMESTAMP)\b", re.I),
              "SYSDATE -> now()::timestamp(0); SYSTIMESTAMP -> current_timestamp."),
    Construct("DUAL", re.compile(r"\bFROM\s+dual\b", re.I),
              "FROM DUAL -> omit the FROM clause entirely."),
    Construct("MERGE", re.compile(r"\bMERGE\s+INTO\b", re.I),
              "MERGE -> INSERT ... ON CONFLICT DO UPDATE. Needs a unique "
              "constraint to conflict on."),
    Construct("TO_CHAR_MASK",
              re.compile(r"\bTO_CHAR\s*\([^)]*'[^']*(RR|HH24|MON)[^']*'", re.I),
              "Oracle format mask. RR is a Y2K-era two-digit year window with no "
              "PostgreSQL equivalent; MON is locale-dependent."),
    Construct("ADD_MONTHS", re.compile(r"\bADD_MONTHS\s*\(", re.I),
              "ADD_MONTHS(d,n) -> d + make_interval(months => n). Verify "
              "end-of-month clamping rather than assuming it matches."),
    Construct("TRUNC_DATE", re.compile(r"\bTRUNC\s*\(\s*SYSDATE", re.I),
              "TRUNC(SYSDATE) -> date_trunc('day', now())."),
    Construct("DATE_SUBTRACT",
              re.compile(r"\b\w*date\w*\s*-\s*(TRUNC\s*\(\s*SYSDATE|\w*date\w*)\b", re.I),
              "date - date returns a NUMBER of days in Oracle but an INTERVAL in "
              "PostgreSQL. Comparing an interval to an integer does not fail at "
              "translation time -- it fails in production."),
    Construct("PACKAGE_CALL", re.compile(r"\bpkg_\w+\.\w+\s*\(", re.I),
              "Package call. Valid after migration only if the converter created "
              "a SCHEMA of that name containing the function."),
    Construct("BULK_COLLECT", re.compile(r"\bBULK\s+COLLECT\b", re.I),
              "BULK COLLECT -> array_agg or a set-returning function."),
    Construct("FORALL", re.compile(r"\bFORALL\s+\w+\s+IN\b", re.I),
              "FORALL -> a single set-based UPDATE or INSERT."),
    Construct("AUTONOMOUS", re.compile(r"\bPRAGMA\s+AUTONOMOUS_TRANSACTION\b", re.I),
              "NO PostgreSQL equivalent. The pragma exists so the row commits "
              "even when the caller rolls back -- exactly what an audit log "
              "needs. Dropping it compiles, runs, and silently inverts the "
              "semantics. Refuse and queue for redesign: dblink, a background "
              "worker, or writing the audit row outside the transaction.",
              translatable=False),
    Construct("SQLPLUS_DIRECTIVE",
              re.compile(r"^\s*(SET|WHENEVER|EXIT|SPOOL)\b", re.I | re.M),
              "SQL*Plus directive, not SQL -> psql meta-command "
              "(\\set ON_ERROR_STOP 1 etc.). Do not translate as a statement."),
    Construct("ROWID", re.compile(r"\bROWID\b", re.I),
              "ROWID -> ctid, but ctid is not stable across VACUUM. Storing one "
              "at all usually signals a design that needs revisiting.",
              translatable=False),
    Construct("VARCHAR2", re.compile(r"\bVARCHAR2\s*\(", re.I),
              "VARCHAR2(n BYTE|CHAR) -> varchar(n). BYTE semantics change "
              "meaning for multibyte text."),
]

BY_LABEL = {c.label: c for c in CONSTRUCTS}

# Anything here must be refused, not translated.
UNTRANSLATABLE = {c.label for c in CONSTRUCTS if not c.translatable}

SOURCE_SUFFIXES = (".py", ".java", ".sql", ".xml", ".jsp", ".properties")


def find(text: str) -> list[Construct]:
    """Every construct present in a chunk of SQL or source."""
    return [c for c in CONSTRUCTS if c.found_in(text)]


def must_refuse(text: str) -> list[Construct]:
    """Constructs that have no safe translation.

    A non-empty result means the correct output is a refusal with an
    explanation, not a conversion. A confident wrong translation of an
    autonomous transaction is worse than no translation at all, because it
    passes review.
    """
    return [c for c in find(text) if not c.translatable]


def scan_text(text: str, path: str = "<text>") -> list[dict]:
    """Locate every construct occurrence, with line numbers.

    Line-level rather than file-level because the deliverable is a diff, and a
    diff needs to point at a line.
    """
    hits: list[dict] = []
    for construct in CONSTRUCTS:
        for match in construct.pattern.finditer(text):
            line_no = text.count("\n", 0, match.start()) + 1
            line = text.splitlines()[line_no - 1] if text else ""
            hits.append({
                "path": path,
                "line": line_no,
                "construct": construct.label,
                "translatable": construct.translatable,
                "note": construct.note,
                "source": line.strip()[:120],
            })
    return sorted(hits, key=lambda h: (h["path"], h["line"], h["construct"]))


def scan_file(path: str) -> list[dict]:
    try:
        with open(path, encoding="utf-8", errors="replace") as handle:
            return scan_text(handle.read(), path)
    except OSError as exc:
        print(f"cannot read {path}: {exc}", file=sys.stderr)
        return []


def scan_dir(root: str) -> list[dict]:
    hits: list[dict] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in {"__pycache__", ".git", "target"}]
        for name in sorted(filenames):
            if name.endswith(SOURCE_SUFFIXES):
                hits.extend(scan_file(os.path.join(dirpath, name)))
    return hits


def _report(hits: list[dict]) -> int:
    if not hits:
        print("No Oracle-specific constructs found.")
        return 0

    by_path: dict[str, list[dict]] = {}
    for hit in hits:
        by_path.setdefault(hit["path"], []).append(hit)

    refuse_total = 0
    for path, path_hits in by_path.items():
        print(f"\n{path}")
        for hit in path_hits:
            marker = "REFUSE " if not hit["translatable"] else "       "
            print(f"  {marker}{hit['line']:>5}  {hit['construct']}")
            print(f"           {hit['source']}")
            if not hit["translatable"]:
                refuse_total += 1

    distinct = {h["construct"] for h in hits}
    print(f"\n{len(hits)} occurrences, {len(distinct)} distinct constructs, "
          f"across {len(by_path)} files.")
    if refuse_total:
        print(f"{refuse_total} marked REFUSE -- these have no safe mechanical "
              f"translation. Write a MANUAL_REVIEW.md instead of converting.")
    return 0


def _self_test() -> int:
    """Each case is a construct that has actually been mistranslated somewhere."""
    cases = [
        ("SELECT * FROM t WHERE ROWNUM <= 10", "ROWNUM", True),
        ("SELECT a FROM t1, t2 WHERE t1.id = t2.id (+)", "OUTER_JOIN_PLUS", True),
        ("SELECT NVL(x, 0) FROM t", "NVL", True),
        ("SELECT DECODE(s, 'A', 1, 0) FROM t", "DECODE", True),
        ("SELECT SYSDATE FROM dual", "DUAL", True),
        ("MERGE INTO t USING s ON (t.id = s.id)", "MERGE", True),
        ("PRAGMA AUTONOMOUS_TRANSACTION;", "AUTONOMOUS", False),
        ("SELECT ROWID FROM t", "ROWID", False),
        ("SET ON_ERROR_STOP 1", "SQLPLUS_DIRECTIVE", True),
        ("BEGIN SELECT x BULK COLLECT INTO v FROM t; END;", "BULK_COLLECT", True),
    ]
    failures = 0
    for text, expected_label, expected_translatable in cases:
        labels = {c.label for c in find(text)}
        if expected_label not in labels:
            failures += 1
            print(f"FAIL {text!r}: expected {expected_label}, got {sorted(labels) or 'nothing'}")
            continue
        actual = BY_LABEL[expected_label].translatable
        if actual is not expected_translatable:
            failures += 1
            print(f"FAIL {expected_label}: translatable={actual}, "
                  f"expected {expected_translatable}")

    # The refusal set is the load-bearing part -- assert it explicitly.
    if UNTRANSLATABLE != {"AUTONOMOUS", "ROWID"}:
        failures += 1
        print(f"FAIL untranslatable set drifted: {sorted(UNTRANSLATABLE)}")

    print(f"{len(cases) - failures}/{len(cases)} passed")
    return 1 if failures else 0


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

    if args.file:
        hits = scan_file(args.file)
    elif args.dir:
        hits = scan_dir(args.dir)
    else:
        parser.print_help()
        return 2

    if args.refuse_only:
        hits = [h for h in hits if not h["translatable"]]

    if args.json:
        print(json.dumps(hits, indent=2))
        return 0
    return _report(hits)


if __name__ == "__main__":
    sys.exit(main())
