---
name: nullability-preservation
description: This skill should be used whenever rows move from Oracle to PostgreSQL or a completed load is being verified — when asked to "load a table", "copy the data", "run pg_copy_load", "check the migration", or "compare NULL counts". Oracle collapses the empty string into NULL and PostgreSQL does not; this skill defines how to preserve that distinction on load and how to prove it afterwards.
allowed-tools: [Read, Bash, mcp__oracle_src__oracle_row_count, mcp__oracle_src__oracle_sample_rows, mcp__pg_target__pg_copy_load, mcp__pg_target__pg_query, mcp__pg_target__pg_row_count, mcp__migration_local__write_artifact]
---

# Preserving NULL across the Oracle → PostgreSQL boundary

**Loaded by two phases.** Phase 3 uses it to load correctly; phase 5 uses it to prove the load
was correct. That is deliberate: the check and the thing being checked must agree on what
"correct" means, and the way to guarantee that is for both to read the same file.

---

## The trap

Oracle has no empty string. `''` **is** `NULL` — the same value, indistinguishable, not merely
equal:

```sql
-- Oracle: returns 'yes'
SELECT CASE WHEN '' IS NULL THEN 'yes' ELSE 'no' END FROM dual;
```

PostgreSQL treats `''` and `NULL` as different values. So a round trip that does not say what
to do with empty fields can turn 1,412 NULLs into 1,412 zero-length strings.

Nothing errors. Row counts match. Checksums over the text values match, because `''` and `NULL`
often serialise identically in a CSV. **Every structural check passes and the data is wrong.**

What breaks is downstream:

```sql
SELECT COUNT(*) FROM ucc_debtor WHERE mailing_address_2 IS NULL;
-- Oracle:      1412
-- PostgreSQL:     0     <- if the load wrote '' instead of NULL
```

`app/filing_repository.py` has exactly this query. It does not need rewriting — it is already
valid PostgreSQL. It simply starts returning nothing.

---

## Loading (phase 3)

**Set `null_as` explicitly on every `pg_copy_load` call.** Not once at the top of the run — per
call. A default that is right today is a default someone changes.

```python
pg_copy_load(
    table="ucc_debtor",
    csv_path=...,
    null_as="\\N",       # the sentinel that appears in the CSV for NULL
    batch_size=10000,
)
```

The sentinel must be a string that cannot occur as real data. `\N` is the PostgreSQL `COPY`
default and is the right choice unless the data genuinely contains it.

Two more load-side rules:

- **CLOB and BLOB out of band.** Inlining a BLOB into a CSV corrupts the row on any byte that
  collides with the delimiter or the quote character. Load them separately, keyed by id.
- **Largest table first.** `UCC_DEBTOR` (7,418 rows) before the small ones, so a capacity or
  encoding problem surfaces in minute two rather than minute forty.

---

## Proving it (phase 5)

A row count is not proof. Run the comparison:

```bash
python .claude/skills/nullability-preservation/scripts/compare_nulls.py \
    --table ucc_debtor --column mailing_address_2 \
    --oracle-nulls 1412 --pg-nulls <n> --pg-empty <n>
```

Or against the whole expected profile:

```bash
python .claude/skills/nullability-preservation/scripts/compare_nulls.py \
    --profile ../legacy-oracle/fixtures/checksum_ucc_debtor.json --observed artifacts/pg_profile.json
```

The rule it enforces, which you should be able to state without the script:

> For every column, `oracle_nulls` must equal `pg_nulls`, **and** `pg_empty_strings` must be
> zero — unless the column genuinely held empty strings in a source that distinguishes them,
> which Oracle never does.

A non-zero empty-string count on a column that was NULL in Oracle is a **defect**, not a
warning. It does not get averaged into a pass rate.

---

## The reporting rule

This is the one that decides whether the validation is worth running at all.

**Report the defect by name. Do not average it away.**

"142 of 148 checks passed (96%)" is a sentence that hides a broken load. The six failures are
the entire content of the report. Write:

```
DEFECTS (1)
  ucc_debtor.mailing_address_2
    Oracle NULL count:        1412
    PostgreSQL NULL count:       0
    PostgreSQL '' count:      1412
    -> the load wrote empty strings where Oracle had NULL.
       filing_repository.debtors_missing_address_line_2 now returns 0 rows.
```

If you are validating in the same context that performed the load, you have already seen the
reasoning that produced it, and you will be inclined to accept it. **Re-derive the counts from
the database rather than from what you remember writing.** That inclination is the known cost
of this architecture — see `evaluation/architecture_comparison.md`.
