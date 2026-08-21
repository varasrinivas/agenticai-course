"""The registry of Oracle constructs that do not survive a move to PostgreSQL.

Kept separate from `tools_local.py` on purpose: this is the part with no
SDK dependency, so it can be unit-tested in milliseconds without an API
key, a database, or the agent framework installed. `tools_local.scan_app_sql`
imports it; so do the tests.

Each entry carries a `translatable` flag. `False` means there is no correct
mechanical translation and the converter must refuse rather than guess --
`PRAGMA AUTONOMOUS_TRANSACTION` being the case that matters.
"""

from __future__ import annotations

import re
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
