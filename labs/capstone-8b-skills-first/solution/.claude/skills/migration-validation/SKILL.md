---
name: migration-validation
description: This skill should be used when proving a completed Oracle-to-PostgreSQL migration is correct, or locating exactly where it is not — when asked to "validate the migration", "reconcile the tables", "check the load", "run the six checks", or to produce a validation report or defect list. Defines the six checks, the order to run them, and the reporting rules that stop a real defect being averaged away.
allowed-tools: [Read, Bash, mcp__oracle_src__oracle_row_count, mcp__oracle_src__oracle_checksum, mcp__oracle_src__oracle_sample_rows, mcp__pg_target__pg_row_count, mcp__pg_target__pg_checksum, mcp__pg_target__pg_query, mcp__migration_local__write_artifact]
---

# Proving the migration

## Your job is adversarial

Every other phase of this pipeline was trying to make the migration succeed. This one is trying
to find what those phases missed.

**A validator that reports "all clear" on a broken load is worse than no validator**, because it
converts an open question into a false answer, and the next person to look is a customer.

### The bias you are running with

In the subagent build of this migration, validation ran in its own context and had never seen
the loading decisions. **Here it does not.** You are the same context that chose the type
mappings and ran the loads. You will be inclined to accept your own work.

Two rules follow, and they are not optional:

1. **Re-derive every number from the database.** Never report a count you remember writing.
   If you did not just query it, you do not know it.
2. **Assume the load is broken until a query says otherwise.** Start from suspicion, not from
   your recollection that phase 3 went fine.

`evaluation/architecture_comparison.md` measures whether these rules actually hold. Be honest
in it — a comparison that flatters this architecture makes the whole capstone worthless.

---

## The six checks

Run all six, per table, in this order. Load `references/check-catalog.md` for the query for each.

| # | Check | Catches |
|---|---|---|
| 1 | Row count | Truncated or duplicated loads |
| 2 | Column checksum | Value corruption at scale |
| 3 | Per-column NULL count | Dropped values |
| 4 | Per-column empty-string count (PostgreSQL only) | **The empty-string trap** |
| 5 | Foreign-key integrity | Orphans from out-of-order loads |
| 6 | 20-row spot-check diff | Everything the aggregates hide |

Checks 1 and 2 are the ones that pass on a broken migration. **Do not stop when they are
green.** Check 4 has no Oracle counterpart to compare against — Oracle has no empty string — so
it is a one-sided assertion: the count must be zero.

Check 6 is the only one that catches `DATE` → `date` truncation. A checksum computed over
already-truncated values agrees with itself perfectly.

For checks 3 and 4, use the shared skill rather than reimplementing the rule:

```bash
python .claude/skills/nullability-preservation/scripts/compare_nulls.py \
    --profile ../legacy-oracle/fixtures/checksum_ucc_debtor.json \
    --observed artifacts/pg_profile.json
```

---

## Reporting

Two severities, and the distinction is load-bearing:

- **BLOCKER** — the migration caused it. Cutover must not proceed.
- **WARNING** — real, but present in the Oracle source too. Raise it so that whoever reads the
  data next does not mistake it for a migration bug.

`ucc_filing.status` has an ACTIVE row with a lapse_date in the past. That drift exists in
Oracle. It is a WARNING, not a BLOCKER — and reporting it as a BLOCKER is its own kind of
failure, because a validator that cries wolf gets skipped.

### Never emit a percentage

"142 of 148 checks passed (96%)" is how a broken load reaches production. The six failures are
the report; the 142 are not. Name every defect, with its table, its column, and its
consequence:

```
DEFECTS (1)
  [BLOCKER] empty_string_divergence -- ucc_debtor.mailing_address_2
      Oracle NULL count:     1412
      PostgreSQL NULL count:    0
      PostgreSQL '' count:   1412
      -> Every IS NULL query against this column now returns fewer rows.
         filing_repository.debtors_missing_address_line_2 returns 0.
         Re-load with null_as set.
```

---

## Expect the first run to fail

On a first pass, check 4 on `ucc_debtor.mailing_address_2` is **supposed** to come back red,
because nothing has yet forced `null_as` on the load. That is the exercise.

Fix it in `nullability-preservation/SKILL.md`, then:

```bash
python coordinator.py --phase data
python coordinator.py --phase validate
```

**If your first run comes back clean, do not celebrate — verify the validator actually ran.**
An empty defect list and a validator that never executed are indistinguishable in the JSON.
Check `migration_audit.jsonl` for the tool calls, and confirm
`artifacts/validation_summary.json` has a non-zero `checks_passed`.

---

## Output

`artifacts/validation_summary.json` with keys `tables_validated`, `checks_passed`,
`checks_failed`, and `defects[]` — each defect carrying `severity`, `check`, `table`, `column`,
`observed`, `expected`, and `consequence`.

Then the console dashboard, which is what a human actually reads. Per-table reconciliation with
one row per table and one column per check, so a red cell is findable in one glance.
