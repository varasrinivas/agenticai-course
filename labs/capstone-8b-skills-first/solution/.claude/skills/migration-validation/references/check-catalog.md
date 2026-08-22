# The six checks, with queries

Load this when running phase 5. Each check names what it catches **and what it cannot** — the
second half is the part that matters, because the checks that pass on a broken migration are
the ones people stop at.

---

## 1. Row count

```sql
-- Oracle
SELECT COUNT(*) FROM meridian.ucc_debtor;
-- PostgreSQL
SELECT COUNT(*) FROM ucc_migrated.ucc_debtor;
```

**Catches:** truncated loads, duplicated batches, a batch loop that exited early.
**Misses:** everything about the *contents*. Equal counts of wrong rows is a pass.

## 2. Column checksum

```sql
-- Oracle
SELECT SUM(ORA_HASH(debtor_name || '|' || city)) FROM meridian.ucc_debtor;
-- PostgreSQL
SELECT SUM(hashtext(debtor_name || '|' || city)::bigint) FROM ucc_migrated.ucc_debtor;
```

The hash functions differ between the engines, so **compare a checksum to itself across a
re-run, not across the two databases.** For cross-engine comparison, checksum a canonical
projection — a sorted, delimited string of the columns you care about — computed the same way on
both sides.

**Catches:** value corruption at scale, encoding damage, column ordering mistakes.
**Misses:** anything that damaged *both* sides identically. Critically, a `DATE` → `date`
truncation is already applied to every value before the checksum is taken, so the checksum
agrees with itself and reports green.

**Misses:** NULL vs `''`. Both frequently serialise to the same thing in the projection.

## 3. Per-column NULL count

```sql
-- Oracle
SELECT COUNT(*) FROM meridian.ucc_debtor WHERE mailing_address_2 IS NULL;
-- PostgreSQL
SELECT COUNT(*) FROM ucc_migrated.ucc_debtor WHERE mailing_address_2 IS NULL;
```

Run for **every nullable column**, not just the suspicious one. The point of a systematic check
is to find the defect you were not looking for.

**Catches:** dropped values, and half of the empty-string trap.
**Misses:** the other half — see check 4.

## 4. Per-column empty-string count — PostgreSQL only

```sql
SELECT COUNT(*) FROM ucc_migrated.ucc_debtor WHERE mailing_address_2 = '';
```

There is **no Oracle counterpart**, and that is not an oversight. Oracle has no empty string —
`''` is `NULL`. So this is a one-sided assertion rather than a comparison:

> The count must be zero. Any non-zero result was manufactured by the load.

**Catches:** the empty-string trap, which is the defect this whole lab is built around.
**Misses:** nothing in its lane. This is the sharpest check of the six.

Use the shared script rather than hand-rolling the comparison, so the loader and the validator
cannot drift apart on what "correct" means:

```bash
python .claude/skills/nullability-preservation/scripts/compare_nulls.py \
    --profile ../legacy-oracle/fixtures/checksum_ucc_debtor.json \
    --observed artifacts/pg_profile.json
```

## 5. Foreign-key integrity

```sql
SELECT COUNT(*) FROM ucc_migrated.ucc_debtor d
 WHERE NOT EXISTS (SELECT 1 FROM ucc_migrated.ucc_filing f
                    WHERE f.filing_id = d.filing_id);
```

**Catches:** orphans from loading children before parents, or from a parent batch that failed
while a child batch succeeded.
**Misses:** orphans that exist in Oracle too. Check the source before calling one a defect —
legacy schemas frequently carry orphans that predate the constraint.

## 6. Twenty-row spot-check diff

```sql
-- both sides, same ordering, same projection
SELECT filing_id, filed_date, lapse_date, status
  FROM ucc_filing ORDER BY filing_id FETCH FIRST 20 ROWS ONLY;   -- Oracle
SELECT filing_id, filed_date, lapse_date, status
  FROM ucc_migrated.ucc_filing ORDER BY filing_id LIMIT 20;      -- PostgreSQL
```

Compare **values**, not counts. This is the only check that sees:

- `DATE` → `date` truncation (`14:32:07` became `00:00:00`)
- timezone shifts from `TIMESTAMP WITH LOCAL TIME ZONE`
- trailing-space differences from `char(n)` blank padding
- numeric scale loss from a `NUMBER` mapped to an integer type

Pick the 20 rows deliberately: the first rows by primary key, plus any row the earlier phases
flagged. Twenty random rows from a 7,418-row table will not contain the 1,412 affected ones
reliably enough to trust.

**Catches:** everything the aggregates hide.
**Misses:** anything outside the 20 rows. It is a smoke test, not a proof — which is why it runs
last, after the aggregate checks have narrowed where to look.

---

## Order matters

Run 1 → 6 in order. Each narrows the search space for the next: a row-count mismatch makes a
checksum mismatch uninformative, and there is no point diffing 20 rows of a table that is
missing half its data. Report a failure at any level, then **keep going** — one broken table
does not excuse skipping the other five.
