"""The Oracle -> PostgreSQL type mapping, as code.

Why this is a module and not just a paragraph in the subagent prompt: a
mapping table written only in a prompt cannot be unit-tested, cannot be
diffed when someone changes it, and produces a different answer on a bad
day. Encoding the mechanical part here means the model spends its
judgement on the cases that actually need judgement -- is this RAW(16) a
UUID? does this unconstrained NUMBER ever carry a scale? -- and not on
remembering whether NUMBER(9) fits in an int.

`map_type()` returns a `Mapping` carrying the target type, a reason, and a
confidence. Anything below `CONFIDENT` is a prompt for the model to look
at the data before committing.
"""

from __future__ import annotations

import re
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
