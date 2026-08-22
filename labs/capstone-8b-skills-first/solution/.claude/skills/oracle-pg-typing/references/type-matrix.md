# The full Oracle → PostgreSQL 16 type matrix

Load this when you need a type that `SKILL.md` does not name, or when you want to justify a
mapping in a decision log. `scripts/check_mapping.py` implements every row here — if this table
and the script disagree, **the script is authoritative** and this file is the bug.

Confidence column: `C` = confident (mechanical), `D` = check the data, `M` = manual decision.

## Numeric

| Oracle | PostgreSQL | ? | Why |
|---|---|---|---|
| `NUMBER(p)` p ≤ 4 | `smallint` | C | Fits in 2 bytes |
| `NUMBER(p)` p ≤ 9 | `integer` | C | Fits in 4 bytes |
| `NUMBER(p)` p ≤ 18 | `bigint` | C | Fits in 8 bytes |
| `NUMBER(p)` p > 18 | `numeric(p)` | C | Exceeds bigint range |
| `NUMBER(p,s)` s > 0 | `numeric(p,s)` | C | Exact decimal — money or a rate |
| `NUMBER(p,s)` s < 0 | `numeric` | M | Negative scale rounds *left* of the decimal point. PostgreSQL has no equivalent; the rounding must move into the application |
| `NUMBER` (bare) | `numeric` | D | May carry a scale. Narrowing to an integer type truncates silently |
| `FLOAT` | `double precision` | C | Oracle `FLOAT` is a `NUMBER` in disguise; check precision if exactness matters |
| `BINARY_FLOAT` | `real` | C | Both IEEE 754 single |
| `BINARY_DOUBLE` | `double precision` | C | Both IEEE 754 double |

## Character

| Oracle | PostgreSQL | ? | Why |
|---|---|---|---|
| `VARCHAR2(n CHAR)` | `varchar(n)` | C | CHAR semantics match directly |
| `VARCHAR2(n BYTE)` | `varchar(n)` | D | Oracle counts bytes, PostgreSQL counts characters. Widen if the data holds non-ASCII |
| `CHAR(n)` / `NCHAR(n)` | `char(n)` | C | Blank-padded comparison preserved |
| `CLOB` / `NCLOB` | `text` | C | PostgreSQL `text` is unbounded |
| `LONG` | `text` | C | Deprecated in Oracle too |

## Date and time

| Oracle | PostgreSQL | ? | Why |
|---|---|---|---|
| `DATE` | **`timestamp(0)`** | C | **Not `date`.** Oracle `DATE` carries a time component |
| `TIMESTAMP(n)` | `timestamp(n)` | C | Direct |
| `TIMESTAMP(n) WITH TIME ZONE` | `timestamptz(n)` | C | Direct |
| `TIMESTAMP(n) WITH LOCAL TIME ZONE` | `timestamptz(n)` | D | Closest available. Oracle renders LTZ in the *session's* zone; PostgreSQL always in the *client's*. Behaviour changes for clients in another zone |
| `INTERVAL ...` | `interval` | C | Direct |

## Binary and large objects

| Oracle | PostgreSQL | ? | Why |
|---|---|---|---|
| `RAW(16)` holding GUIDs | `uuid` | D | Only if the bytes are GUIDs. A 16-byte hash is `bytea` — the DDL cannot tell you which |
| `RAW(n)` n ≠ 16 | `bytea` | C | Arbitrary binary |
| `LONG RAW` | `bytea` | C | Deprecated in Oracle too |
| `BLOB` | `bytea` | C | Load out of band, **not** inline in CSV |
| `BFILE` | `text` | M | External file reference. No equivalent — store the path, move the file separately |

## Identifiers and oddities

| Oracle | PostgreSQL | ? | Why |
|---|---|---|---|
| `ROWID` / `UROWID` | `text` | M | `ctid` is not stable across `VACUUM`. Storing a ROWID at all usually signals a design that needs revisiting |
| `XMLTYPE` | `xml` | C | Direct |
| anything unlisted | `text` | M | Defaulting to `text` is a placeholder, not an answer |

## Identifier case

Oracle folds unquoted identifiers to UPPER; PostgreSQL folds to lower. **Lowercase and do not
quote.** Quoting `"UCC_FILING"` preserves the uppercase name and forces every hand-written query
afterwards to quote it too, permanently.
