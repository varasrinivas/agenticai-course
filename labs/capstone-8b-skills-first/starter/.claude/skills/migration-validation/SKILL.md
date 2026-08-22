---
name: migration-validation
description: This skill should be used when proving a completed Oracle-to-PostgreSQL migration is correct, or locating exactly where it is not — when asked to "validate the migration", "reconcile the tables", "check the load", "run the six checks", or to produce a validation report or defect list. Defines the six checks, the order to run them, and the reporting rules that stop a real defect being averaged away.
allowed-tools: [Read, Bash, mcp__oracle_src__oracle_row_count, mcp__oracle_src__oracle_checksum, mcp__oracle_src__oracle_sample_rows, mcp__pg_target__pg_row_count, mcp__pg_target__pg_checksum, mcp__pg_target__pg_query, mcp__migration_local__write_artifact]
---

# Proving the migration

## TODO(1) — Set the adversarial stance

Every other phase was trying to make the migration succeed. Write what this one is for, and the
one-sentence claim about why a falsely-clean validator is worse than no validator at all.

## TODO(2) — Name the bias this architecture creates

This is the TODO that does not exist in the subagent version of this lab, and it is the reason
Capstone 8B exists.

In Capstone 8, validation ran as a subagent with its own context and had never seen the loading
decisions. Here it runs in the **same context** that chose the type mappings and ran the loads.

Write down what that changes, then write the two concrete rules that compensate. "Be objective"
is not a rule. Each one should be something an observer could check you actually did.

## TODO(3) — The six checks

Fill in the table. `references/check-catalog.md` is where the queries go — that file is also a
TODO.

| # | Check | Catches | Misses |
|---|---|---|---|
| 1 | row count | | |
| 2 | column checksum | | |
| 3 | per-column NULL count | | |
| 4 | per-column empty-string count | | |
| 5 | foreign-key integrity | | |
| 6 | 20-row spot-check diff | | |

The **Misses** column is the one worth your time. Two of these checks come back green on a
broken migration — identify which, and say so loudly enough that nobody stops there.

Two more things to work out:

- one check has no Oracle counterpart at all. Which, and why?
- one check is the only thing that can catch a `DATE` mapped to `date`. Which, and why do the
  aggregate checks all miss it?

For checks 3 and 4, call the shared script rather than reimplementing the rule:

```bash
python .claude/skills/nullability-preservation/scripts/compare_nulls.py --help
```

Explain why reimplementing it here would be a mistake even though it would be quick.

## TODO(4) — Severity

Define two severities and the test that sorts a finding into one or the other.

`ucc_filing` has an ACTIVE row with a `lapse_date` in the past — and that drift exists in the
Oracle source too. Decide how it is reported, and write the reason. Consider what happens to a
validator that reports source drift at the highest severity.

## TODO(5) — The reporting rule

Write the rule about percentages. Then write the shape of a defect report that makes a single
failure impossible to skim past.

## TODO(6) — Expect the first run to fail

Your first end-to-end run is *supposed* to fail check 4 on `ucc_debtor.mailing_address_2`.
Write the note that tells the student that, how to fix it, and how to re-run.

Then add the warning that matters more: what should a student suspect if their **first** run
comes back completely clean? Tell them how to tell the difference between "passed" and "never
ran".
