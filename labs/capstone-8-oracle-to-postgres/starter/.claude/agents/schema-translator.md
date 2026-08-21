---
name: schema-translator
description: Translates one Oracle table's DDL into PostgreSQL 16 DDL and records a justified type-mapping decision for every column. Use for phase 2 of the migration, one table at a time.
tools: mcp__oracle_src__oracle_get_ddl, mcp__oracle_src__oracle_sample_rows, mcp__pg_target__pg_apply_ddl, mcp__migration_local__write_artifact
model: claude-sonnet-4-6
---

TODO: write this subagent's instructions.

It needs the full type-mapping table (see type_mapping.py, which you also build), the identity/trigger rule, and the no-quoted-identifiers rule.

Two things worth more than completeness here:

1. **Say why, not just what.** A mapping table the subagent can follow
   mechanically produces mechanical output. A table that explains what
   breaks when you get it wrong produces a subagent that notices the case
   you did not list.

2. **Say what to do when it is unsure.** A subagent with no instruction
   for uncertainty will guess, confidently, and the guess will look exactly
   like a correct answer in the report.

The reference version is in `solution/.claude/agents/schema-translator.md`.
Write yours first, then diff -- the differences are the interesting part.
