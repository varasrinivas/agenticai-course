"""The Oracle -> PostgreSQL type mapping, as code, bundled with the skill.

In the subagent build of this migration (Capstone 8) this module sat at the
project root and the mapping *rules* were prose inside
`.claude/agents/schema-translator.md`. The knowledge and the code that
enforces it lived in two places, and only one of them was testable.

Here they ship together. `SKILL.md` says when to apply the mapping and which
traps to watch; this script decides the mechanical part deterministically.
A mapping table written only in a prompt cannot be unit-tested, cannot be
diffed when someone changes it, and produces a different answer on a bad day.
Encoding the mechanical part here means the model spends its judgement on the
cases that actually need judgement -- is this RAW(16) a UUID? does this
unconstrained NUMBER ever carry a scale? -- and not on remembering whether
NUMBER(9) fits in an int.

`map_type()` returns a `Mapping` carrying the target type, a reason, and a
confidence. Anything below `CONFIDENT` is a prompt for the model to look at
the data before committing.

Run it directly:

    python check_mapping.py --type "NUMBER(9)"
    python check_mapping.py --type "RAW(16)" --sample 3f2504e0-4f89-11d3-9a0c-0305e82c3301
    python check_mapping.py --ddl artifacts/ddl/ucc_filing.sql
    python check_mapping.py --self-test
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


_NUMBER = re.compile(r"^NUMBER\s*(?:\(\s*(\*|\d+)\s*(?:,\s*(-?\d+)\s*)?\))?$", re.I)
_VARCHAR2 = re.compile(r"^VARCHAR2?\s*\(\s*(\d+)\s*(BYTE|CHAR)?\s*\)$", re.I)
_CHAR = re.compile(r"^N?CHAR\s*\(\s*(\d+)\s*(BYTE|CHAR)?\s*\)$", re.I)
_RAW = re.compile(r"^RAW\s*\(\s*(\d+)\s*\)$", re.I)
_TIMESTAMP = re.compile(r"^TIMESTAMP\s*(?:\(\s*(\d+)\s*\))?(.*)$", re.I)


def map_type(oracle_type: str, *, sample_values: list | None = None) -> Mapping:
    """Map one Oracle column type to PostgreSQL.

    `sample_values` is optional but changes the answer for RAW(16): 16
    binary bytes that are all UUID-shaped are a `uuid`; 16 binary bytes
    that are a hash are `bytea`. The DDL alone cannot tell you which.
    """
    declared = (oracle_type or "").strip()
    upper = declared.upper()

    # ---- NUMBER ------------------------------------------------------
    number = _NUMBER.match(upper)
    if number:
        precision_raw, scale_raw = number.group(1), number.group(2)

        if precision_raw is None or precision_raw == "*":
            return Mapping(
                declared, "numeric",
                "NUMBER with no declared precision can carry a scale; narrowing "
                "it to an integer type would silently truncate.",
                Confidence.CHECK_DATA,
            )

        precision = int(precision_raw)
        scale = int(scale_raw) if scale_raw is not None else 0

        if scale > 0:
            return Mapping(declared, f"numeric({precision},{scale})",
                           "Exact decimal preserved -- this is money or a rate.")
        if scale < 0:
            return Mapping(declared, "numeric",
                           f"Negative scale ({scale}) rounds left of the decimal "
                           f"point; PostgreSQL has no equivalent, so the "
                           f"rounding must move into the application.",
                           Confidence.MANUAL)
        if precision <= 4:
            return Mapping(declared, "smallint", f"NUMBER({precision}) fits in 2 bytes.")
        if precision <= 9:
            return Mapping(declared, "integer", f"NUMBER({precision}) fits in 4 bytes.")
        if precision <= 18:
            return Mapping(declared, "bigint", f"NUMBER({precision}) fits in 8 bytes.")
        return Mapping(declared, f"numeric({precision})",
                       f"NUMBER({precision}) exceeds bigint range.")

    # ---- character ---------------------------------------------------
    varchar = _VARCHAR2.match(upper)
    if varchar:
        length, semantics = int(varchar.group(1)), (varchar.group(2) or "BYTE").upper()
        if semantics == "BYTE":
            return Mapping(
                declared, f"varchar({length})",
                f"PostgreSQL counts characters, Oracle BYTE semantics count "
                f"bytes. For multibyte text a value that fit in "
                f"{length} bytes may need more than {length} characters -- "
                f"widen if the data contains non-ASCII.",
                Confidence.CHECK_DATA,
            )
        return Mapping(declared, f"varchar({length})", "CHAR semantics match directly.")

    char = _CHAR.match(upper)
    if char:
        return Mapping(declared, f"char({int(char.group(1))})",
                       "Blank-padded comparison semantics are preserved.")

    # ---- date and time -----------------------------------------------
    if upper == "DATE":
        return Mapping(
            declared, "timestamp(0)",
            "Oracle DATE carries a TIME component. Mapping it to `date` "
            "silently truncates 14:32:07 to midnight, which changes which "
            "rows appear to have lapsed.",
        )

    timestamp = _TIMESTAMP.match(upper)
    if timestamp:
        precision = timestamp.group(1)
        qualifier = (timestamp.group(2) or "").strip()
        suffix = f"({precision})" if precision else ""
        if "LOCAL TIME ZONE" in qualifier:
            return Mapping(
                declared, f"timestamptz{suffix}",
                "Closest available type. Oracle renders LTZ in the session's "
                "zone on read; PostgreSQL always renders in the client's. "
                "Behaviour changes for clients in a different zone.",
                Confidence.CHECK_DATA,
            )
        if "TIME ZONE" in qualifier:
            return Mapping(declared, f"timestamptz{suffix}", "Direct equivalent.")
        return Mapping(declared, f"timestamp{suffix}", "Direct equivalent.")

    if upper.startswith("INTERVAL"):
        return Mapping(declared, "interval", "Direct equivalent.")

    # ---- binary and large objects ------------------------------------
    raw = _RAW.match(upper)
    if raw:
        length = int(raw.group(1))
        if length == 16:
            looks_like_uuid = bool(sample_values) and all(
                isinstance(v, str) and len(v.replace("-", "")) == 32
                for v in sample_values
                if v is not None
            )
            if looks_like_uuid:
                return Mapping(declared, "uuid",
                               "RAW(16) holding SYS_GUID values is a uuid.")
            return Mapping(
                declared, "uuid",
                "RAW(16) is usually SYS_GUID -- but confirm against real rows. "
                "If the bytes are a hash rather than a GUID, use bytea.",
                Confidence.CHECK_DATA,
            )
        return Mapping(declared, "bytea", f"RAW({length}) is arbitrary binary.")

    simple = {
        "CLOB": ("text", "Direct equivalent; PostgreSQL text is unbounded."),
        "NCLOB": ("text", "Direct equivalent."),
        "BLOB": ("bytea", "Direct equivalent, but load it out of band, not inline in CSV."),
        "BFILE": ("text", "External file reference; PostgreSQL has no equivalent "
                          "-- store the path and move the file separately."),
        "LONG": ("text", "Deprecated in Oracle too."),
        "LONG RAW": ("bytea", "Deprecated in Oracle too."),
        "BINARY_FLOAT": ("real", "Both IEEE 754 single precision."),
        "BINARY_DOUBLE": ("double precision", "Both IEEE 754 double precision."),
        "FLOAT": ("double precision", "Oracle FLOAT is a NUMBER in disguise; "
                                      "check the precision if exactness matters."),
        "ROWID": ("text", "ctid is not stable across VACUUM. Storing a ROWID at "
                          "all is usually a design that needs revisiting."),
        "UROWID": ("text", "Same caveat as ROWID."),
        "XMLTYPE": ("xml", "Direct equivalent."),
    }
    if upper in simple:
        target, reason = simple[upper]
        confidence = (
            Confidence.MANUAL if upper in {"ROWID", "UROWID", "BFILE"}
            else Confidence.CONFIDENT
        )
        return Mapping(declared, target, reason, confidence)

    return Mapping(declared, "text",
                   f"No mapping rule for {declared!r}. Defaulting to text is a "
                   f"placeholder, not an answer -- a human must decide.",
                   Confidence.MANUAL)


def quote_policy(identifier: str) -> str:
    """Oracle folds unquoted identifiers to upper; PostgreSQL folds to lower.

    So the migration lowercases and does NOT quote. Quoting "UCC_FILING"
    would preserve the uppercase name and force every hand-written query
    afterwards to quote it too -- forever.
    """
    return identifier.lower()


# ---------------------------------------------------------------- CLI
_COLUMN_LINE = re.compile(
    r"^\s*[\"']?(?P<name>\w+)[\"']?\s+"
    r"(?P<type>NUMBER\s*\([^)]*\)|NUMBER|VARCHAR2?\s*\([^)]*\)|N?CHAR\s*\([^)]*\)|"
    r"RAW\s*\([^)]*\)|TIMESTAMP\s*(?:\([^)]*\))?(?:\s+WITH(?:\s+LOCAL)?\s+TIME\s+ZONE)?|"
    r"INTERVAL[^,]*|DATE|CLOB|NCLOB|BLOB|BFILE|LONG\s+RAW|LONG|BINARY_FLOAT|BINARY_DOUBLE|"
    r"FLOAT|UROWID|ROWID|XMLTYPE)",
    re.I | re.M,
)


def columns_from_ddl(ddl: str) -> list[tuple[str, str]]:
    """Pull (column_name, declared_type) pairs out of a CREATE TABLE body.

    Deliberately forgiving: this is a triage aid, not a SQL parser. Anything
    it misses still gets mapped by hand, which is the safe direction to fail.
    """
    skip = {"CREATE", "TABLE", "CONSTRAINT", "PRIMARY", "FOREIGN", "UNIQUE", "CHECK", "USING"}
    out: list[tuple[str, str]] = []
    for match in _COLUMN_LINE.finditer(ddl):
        name = match.group("name")
        if name.upper() in skip:
            continue
        out.append((name, " ".join(match.group("type").split())))
    return out


def _render(name: str | None, mapping: Mapping) -> str:
    flag = {
        Confidence.CONFIDENT: "  ",
        Confidence.CHECK_DATA: "? ",
        Confidence.MANUAL: "! ",
    }[mapping.confidence]
    label = f"{name}  " if name else ""
    return (f"{flag}{label}{mapping.oracle_type}  ->  {mapping.postgres_type}\n"
            f"    [{mapping.confidence.value}] {mapping.reason}")


def _self_test() -> int:
    """The cases that have actually gone wrong on real migrations."""
    cases = [
        ("NUMBER(2)", "smallint", Confidence.CONFIDENT),
        ("NUMBER(9)", "integer", Confidence.CONFIDENT),
        ("NUMBER(18)", "bigint", Confidence.CONFIDENT),
        ("NUMBER(12,2)", "numeric(12,2)", Confidence.CONFIDENT),
        ("NUMBER", "numeric", Confidence.CHECK_DATA),
        ("DATE", "timestamp(0)", Confidence.CONFIDENT),
        ("TIMESTAMP(6) WITH LOCAL TIME ZONE", "timestamptz(6)", Confidence.CHECK_DATA),
        ("RAW(16)", "uuid", Confidence.CHECK_DATA),
        ("RAW(32)", "bytea", Confidence.CONFIDENT),
        ("CLOB", "text", Confidence.CONFIDENT),
        ("ROWID", "text", Confidence.MANUAL),
    ]
    failures = 0
    for declared, expected_type, expected_conf in cases:
        got = map_type(declared)
        ok = got.postgres_type == expected_type and got.confidence is expected_conf
        if not ok:
            failures += 1
            print(f"FAIL {declared}: expected {expected_type}/{expected_conf.value}, "
                  f"got {got.postgres_type}/{got.confidence.value}")
    print(f"{len(cases) - failures}/{len(cases)} passed")
    return 1 if failures else 0


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Map Oracle column types to PostgreSQL 16, with a confidence.")
    parser.add_argument("--type", help="a single Oracle type, e.g. 'NUMBER(9)'")
    parser.add_argument("--ddl", help="path to a file containing Oracle CREATE TABLE DDL")
    parser.add_argument("--sample", nargs="*", default=None,
                        help="sample values; changes the answer for RAW(16)")
    parser.add_argument("--self-test", action="store_true", help="run the built-in cases")
    args = parser.parse_args(argv)

    if args.self_test:
        return _self_test()

    if args.type:
        print(_render(None, map_type(args.type, sample_values=args.sample)))
        return 0

    if args.ddl:
        try:
            ddl = open(args.ddl, encoding="utf-8").read()
        except OSError as exc:
            print(f"cannot read {args.ddl}: {exc}", file=sys.stderr)
            return 2
        columns = columns_from_ddl(ddl)
        if not columns:
            print(f"no column definitions found in {args.ddl}", file=sys.stderr)
            return 1
        review = 0
        for name, declared in columns:
            mapping = map_type(declared)
            review += mapping.needs_review
            print(_render(name, mapping))
        print(f"\n{len(columns)} columns, {review} need a look at the data.")
        return 0

    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
