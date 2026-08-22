---
name: oracle-pg-typing
description: This skill should be used when mapping Oracle column types to PostgreSQL 16 — when the user or the migration asks to "translate a table", "generate DDL", "map this column", "what does NUMBER(9) become", or when any Oracle type name (NUMBER, VARCHAR2, DATE, RAW, CLOB, TIMESTAMP WITH LOCAL TIME ZONE) needs a PostgreSQL equivalent. Provides the mapping procedure, the traps that pass review silently, and a deterministic checker.
allowed-tools: [Read, Bash, mcp__oracle_src__oracle_get_ddl, mcp__oracle_src__oracle_sample_rows, mcp__pg_target__pg_apply_ddl, mcp__migration_local__write_artifact]
---

# Oracle → PostgreSQL type mapping

The frontmatter above is done. **Do not change `name`** — Claude Code resolves a skill by its
directory, and a mismatch makes the skill unreferenceable. `tests/test_skills_wellformed.py`
checks this.

Everything below is yours to write.

> Before you start, read `references/` and `scripts/` in this directory. A skill is three
> things — the procedure (this file), the reference material it defers to, and the executable
> it ships. Writing only this file gets you a prompt, not a skill.

## TODO(1) — State the rule that governs everything else

There is one sentence that determines whether this skill produces correct DDL or plausible DDL.
It is about the difference between what the DDL *declares* and what the rows actually *hold*.

Work out what that sentence is, then say what procedure follows from it. Hint: it implies two
reads per table, not one.

## TODO(2) — Tell the agent to run the checker first

`scripts/check_mapping.py` returns a target type, a reason, and a **confidence** of
`confident` / `check_data` / `manual`.

Write the table that says what to do with each. The interesting instruction is what to do with
`confident`: the agent should *not* re-derive it. Explain why deferring to the script is the
right call rather than a shortcut.

## TODO(3) — The traps

Four mappings in this schema pass every structural check and are still wrong. Find them by
running the checker over `legacy-oracle/01_schema.sql` and looking at what it flags:

```bash
python .claude/skills/oracle-pg-typing/scripts/check_mapping.py --ddl ../legacy-oracle/01_schema.sql
```

For each, write what the naive mapping is, what breaks, and — this is the part that matters —
**why nobody notices**. A trap that announces itself is not a trap.

The one about `DATE` is the most consequential row in the whole migration.

## TODO(4) — Identifier case

Oracle folds unquoted identifiers to UPPER. PostgreSQL folds to lower. Decide what the
migration does about it and write the rule.

This is a one-way door: whichever way you go, every hand-written query afterwards lives with
it. Say so.

## TODO(5) — The identity idiom

The legacy schema predates Oracle 12c, so identity is a sequence plus a `BEFORE INSERT`
trigger. Write the conversion rule, including what has to happen *after* the data load or the
first insert post-cutover collides with an existing key.

Then look at `legacy-oracle/02_sequences_triggers.sql` and count the `BEFORE INSERT` triggers
on `UCC_FILING`. There is more than one, and they do not all have the same fate. Getting this
wrong deletes business logic. Write the rule that stops that.

## TODO(6) — Output contract

Say exactly what files this skill produces per table, and what has to be in the decision log.
Be specific about whether every column gets a line or only the interesting ones — and justify
whichever you choose.
