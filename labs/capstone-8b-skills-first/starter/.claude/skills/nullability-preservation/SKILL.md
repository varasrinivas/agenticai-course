---
name: nullability-preservation
description: This skill should be used whenever rows move from Oracle to PostgreSQL or a completed load is being verified — when asked to "load a table", "copy the data", "run pg_copy_load", "check the migration", or "compare NULL counts". Oracle collapses the empty string into NULL and PostgreSQL does not; this skill defines how to preserve that distinction on load and how to prove it afterwards.
allowed-tools: [Read, Bash, mcp__oracle_src__oracle_row_count, mcp__oracle_src__oracle_sample_rows, mcp__pg_target__pg_copy_load, mcp__pg_target__pg_query, mcp__pg_target__pg_row_count, mcp__migration_local__write_artifact]
---

# Preserving NULL across the Oracle → PostgreSQL boundary

**This is the most important file in the lab.** It is also the one loaded by two different
phases — `coordinator.PHASE_SKILLS` gives it to both the load phase and the validation phase.

Before writing anything, work out why that matters. In the subagent build of this migration the
same knowledge was copy-pasted into two agent prompts. What goes wrong when those two copies
drift, and what does a single shared file buy you? Your answer belongs at the top of this file.

## TODO(1) — Explain the trap

Run this against the seeded Oracle database and explain the result:

```sql
SELECT CASE WHEN '' IS NULL THEN 'yes' ELSE 'no' END FROM dual;
```

Then state what PostgreSQL does differently, and what that difference does to a load that says
nothing about empty fields.

The number you need is in `legacy-oracle/fixtures/checksum_ucc_debtor.json`. Use the real
figure, not "some rows".

## TODO(2) — Show the observable failure

Write the before/after of one concrete query. `app/filing_repository.py` contains a method that
breaks without a single character of its SQL changing — find it.

State plainly why every structural check still passes while this is broken. If you cannot
explain that, the rest of the skill will not convince anyone to follow it.

## TODO(3) — The load-side rule

Write the rule for `pg_copy_load` that prevents the defect. Be specific about:

- which parameter, and what it should be set to
- whether it is set once for the run or per call, and why that choice matters
- what sentinel value is safe, and what makes a sentinel unsafe
- what to do with CLOB and BLOB columns, which must not travel inline in the CSV

## TODO(4) — The proof-side rule

Write the rule the validator checks, as a single testable statement about `oracle_nulls`,
`pg_nulls`, and `pg_empty_strings`. `scripts/compare_nulls.py` has to implement exactly this,
so write it precisely enough to code from.

Note the asymmetry: one half of the rule is a comparison between the two databases, and the
other half is a one-sided assertion about PostgreSQL alone. Explain why the second half has no
Oracle counterpart.

## TODO(5) — The reporting rule

Decide how a failure of this check gets reported, and write the rule.

The temptation is a pass rate. Think about what "142 of 148 checks passed (96%)" communicates
to someone deciding whether to cut over, then write the rule that stops that from happening.

## TODO(6) — Name the bias

Phase 5 runs in the same context that performed the load in phase 3. Write the instruction that
compensates for that. Be concrete about what the agent must do differently, not just that it
should "be careful".
