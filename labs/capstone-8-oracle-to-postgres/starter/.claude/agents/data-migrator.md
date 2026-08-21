---
name: data-migrator
description: Plans and executes a batched extract-and-load for one table, preserving NULL semantics. Use for phase 3 of the migration, one table at a time.
tools: mcp__oracle_src__oracle_row_count, mcp__oracle_src__oracle_sample_rows, mcp__pg_target__pg_copy_load, mcp__pg_target__pg_query, mcp__pg_target__pg_row_count, mcp__migration_local__write_artifact
model: claude-haiku-4-5-20251001
---

TODO: write this subagent's instructions.

It needs the empty-string trap and why null_as must be set explicitly, batching, and LOB handling.

Two things worth more than completeness here:

1. **Say why, not just what.** A mapping table the subagent can follow
   mechanically produces mechanical output. A table that explains what
   breaks when you get it wrong produces a subagent that notices the case
   you did not list.

2. **Say what to do when it is unsure.** A subagent with no instruction
   for uncertainty will guess, confidently, and the guess will look exactly
   like a correct answer in the report.

The reference version is in `solution/.claude/agents/data-migrator.md`.
Write yours first, then diff -- the differences are the interesting part.
