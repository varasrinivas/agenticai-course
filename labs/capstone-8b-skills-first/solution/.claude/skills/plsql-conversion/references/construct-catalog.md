# The Oracle construct catalog

Every construct the migration is expected to meet, what it becomes, and what breaks if you get
it wrong. `../appsql-rewriting/scripts/find_oracleisms.py` detects all of these — this file is
the *why* behind each detection.

**Two entries are marked REFUSE. They have no correct mechanical translation.**

---

## REFUSE — no safe translation

### `PRAGMA AUTONOMOUS_TRANSACTION`

The pragma makes a nested block commit independently of its caller. An audit row written inside
one survives the caller's rollback — which is the entire reason audit code uses it.

PostgreSQL has no in-process equivalent. Options are `dblink` (a loopback connection that is
genuinely a separate transaction), a background worker, or restructuring so the audit write
happens outside the transaction. **All three change the deployment, not just the code.**

Dropping the pragma yields something that compiles and runs and is wrong in the one case it
exists for. Refuse.

### `ROWID`

Maps to `ctid` on paper. But `ctid` is not stable across `VACUUM`, so any code that stores a
ROWID and dereferences it later is broken by the first autovacuum rather than by the migration.
Storing a ROWID at all usually signals a design that needs revisiting. Refuse and flag.

---

## Query shape

| Oracle | PostgreSQL | The trap |
|---|---|---|
| `ROWNUM` | `LIMIT` / `OFFSET` | `ROWNUM` is assigned **before** `ORDER BY`. That is why the Oracle form nests a subquery. `WHERE ROWNUM <= 10 ORDER BY x` is not "top 10 by x" — it is 10 arbitrary rows, then sorted. Reproduce the *intent*, not the syntax |
| `(+)` outer join | `LEFT` / `RIGHT JOIN` | `(+)` marks the **nullable** side, which is the *opposite* side from the one named in `LEFT JOIN`. Getting this backwards silently changes the row count |
| `CONNECT BY` | `WITH RECURSIVE` | `LEVEL` becomes a carried counter; `SYS_CONNECT_BY_PATH` becomes concatenation; `CONNECT_BY_ISLEAF` becomes `NOT EXISTS`; **`ORDER SIBLINGS BY` has no equivalent** and needs a sort key built into the recursion |
| `FROM DUAL` | omit `FROM` entirely | Mechanical |
| `MERGE INTO` | `INSERT ... ON CONFLICT DO UPDATE` | Needs a unique constraint to conflict on. If the Oracle `MERGE` matched on a non-unique predicate, there is no direct equivalent |

## Functions

| Oracle | PostgreSQL | The trap |
|---|---|---|
| `NVL(a,b)` | `COALESCE(a,b)` | Mechanical |
| `NVL2(a,b,c)` | `CASE WHEN a IS NOT NULL THEN b ELSE c END` | Mechanical |
| `DECODE` | `CASE` | **`DECODE` treats `NULL` as matchable; `CASE` does not.** `DECODE(x, NULL, 'none', 'some')` returns `'none'` for a null `x`; the naive `CASE WHEN x = NULL` never matches |
| `SYSDATE` | `now()::timestamp(0)` | `SYSDATE` has no sub-second component; `now()` does. Without the cast you get spurious diffs |
| `SYSTIMESTAMP` | `current_timestamp` | Mechanical |
| `ADD_MONTHS(d,n)` | `d + make_interval(months => n)` | Oracle clamps to end-of-month: `ADD_MONTHS('31-JAN', 1)` is 28-Feb. PostgreSQL does too — **verify, do not assume**, and never on a leap year boundary without a test |
| `TRUNC(SYSDATE)` | `date_trunc('day', now())` | Mechanical |
| `TO_CHAR(d, 'RR...')` | no equivalent | `RR` is a Y2K-era two-digit-year window. `MON` is locale-dependent and will differ under a different `lc_time` |

## Arithmetic

### `date - date`

**The one that reaches production.** In Oracle, subtracting two dates yields a `NUMBER` of days.
In PostgreSQL it yields an `interval`.

```sql
-- Oracle: days_open is a NUMBER. This works.
SELECT filed_date - TRUNC(SYSDATE) AS days_open FROM ucc_filing WHERE ... > 30;

-- PostgreSQL: filed_date - now() is an interval. Comparing it to 30 does not
-- fail at translation time. It fails later, or worse, it compares wrongly.
```

Convert to `EXTRACT(DAY FROM (a - b))` or `(a::date - b::date)` depending on whether the original
meant whole days or elapsed time. **Read the surrounding code to find out which.**

## Bulk operations

| Oracle | PostgreSQL |
|---|---|
| `BULK COLLECT` | `array_agg`, or a set-returning function |
| `FORALL x IN ...` | a single set-based `UPDATE` / `INSERT` |

Both usually simplify. A `FORALL` loop is almost always one statement in PostgreSQL, and the
translated version is faster — resist the urge to reproduce the loop shape.

## Not SQL at all

`SET`, `WHENEVER`, `EXIT`, `SPOOL` are **SQL\*Plus directives**, not statements. They become
`psql` meta-commands (`\set ON_ERROR_STOP 1` and friends). Translating them as SQL produces
syntax errors that look like parser bugs.

`nightly_batch.sql` in this lab opens with a block of them.
