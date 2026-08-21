"""The Oracle -> PostgreSQL type mapping -- YOU BUILD THIS FILE.

Why this is a module and not just a paragraph in the subagent prompt: a
mapping table written only in a prompt cannot be unit-tested, cannot be
diffed when someone changes it, and produces a slightly different answer
on a bad day. Encoding the mechanical part here means the model spends its
judgement on the cases that genuinely need it -- is this RAW(16) a UUID?
does this unconstrained NUMBER ever carry a scale? -- rather than on
recalling whether NUMBER(9) fits in an int.

Verify with:  pytest tests/test_type_mapping.py -v   (46 assertions)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class Confidence(str, Enum):
    CONFIDENT = "confident"     # mechanical, no judgement needed
    CHECK_DATA = "check_data"   # the right answer depends on the values
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

    `sample_values` is optional but changes the answer for RAW(16): sixteen
    binary bytes that are all UUID-shaped are a `uuid`; sixteen bytes that
    are a hash are `bytea`. The DDL alone cannot tell you which, which is
    why the subagent is told to sample rows before deciding.
    """
    declared = (oracle_type or "").strip()
    upper = declared.upper()

    # ---- NUMBER ------------------------------------------------------
    # TODO(2): precision/scale rules.
    #   no precision  -> numeric,      CHECK_DATA (it may carry a scale)
    #   scale > 0     -> numeric(p,s)  (money, rates -- exactness matters)
    #   scale < 0     -> numeric,      MANUAL (no PostgreSQL equivalent)
    #   p <= 4        -> smallint
    #   p <= 9        -> integer
    #   p <= 18       -> bigint
    #   otherwise     -> numeric(p)

    # ---- character ---------------------------------------------------
    # TODO(3): VARCHAR2(n BYTE) and VARCHAR2(n CHAR) both become
    # varchar(n) -- but only the CHAR form is a clean equivalence. Under
    # BYTE semantics a value that fitted in n bytes may need more than n
    # characters once the text is not ASCII, so BYTE gets CHECK_DATA.

    # ---- date and time -----------------------------------------------
    # TODO(4): THE most consequential row in this table.
    #
    #   DATE -> timestamp(0), NOT date.
    #
    # Oracle DATE carries a time component. Mapping it to `date` compiles,
    # loads, and silently truncates 14:32:07 to midnight -- which changes
    # which filings appear to have lapsed. Nothing errors. Put the reason
    # in the Mapping so the decision log explains itself.
    #
    # TIMESTAMP WITH LOCAL TIME ZONE -> timestamptz, CHECK_DATA (Oracle
    # renders LTZ in the session's zone; PostgreSQL in the client's).

    # ---- binary and large objects ------------------------------------
    # TODO(5): RAW(16) -> uuid, but CONFIDENT only when sample_values look
    # UUID-shaped. Other RAW lengths -> bytea. CLOB -> text,
    # BLOB -> bytea, ROWID -> text with MANUAL (ctid is not stable across
    # VACUUM).

    # TODO(6): Unknown type -> text, MANUAL, and say plainly in the reason
    # that this is a placeholder rather than an answer.
    raise NotImplementedError("Build map_type")


def quote_policy(identifier: str) -> str:
    """Oracle folds unquoted identifiers to upper; PostgreSQL folds to lower.

    TODO(7): Return the lowercased name, unquoted. Quoting "UCC_FILING"
    would preserve the uppercase and force every hand-written query
    afterwards to quote it too -- forever.
    """
    raise NotImplementedError("Build quote_policy")
