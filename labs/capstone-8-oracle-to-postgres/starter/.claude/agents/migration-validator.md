---
name: migration-validator
description: Proves the migrated PostgreSQL data is equivalent to the Oracle source, or reports exactly where it is not. Use for phase 5 of the migration.
tools: mcp__oracle_src__oracle_row_count, mcp__oracle_src__oracle_checksum, mcp__oracle_src__oracle_sample_rows, mcp__pg_target__pg_row_count, mcp__pg_target__pg_checksum, mcp__pg_target__pg_query, mcp__migration_local__write_artifact
model: claude-haiku-4-5-20251001
---

TODO: write this subagent's instructions.

It needs the six checks, and the one defect that must never be averaged into a pass rate.

Two things worth more than completeness here:

1. **Say why, not just what.** A mapping table the subagent can follow
   mechanically produces mechanical output. A table that explains what
   breaks when you get it wrong produces a subagent that notices the case
   you did not list.

2. **Say what to do when it is unsure.** A subagent with no instruction
   for uncertainty will guess, confidently, and the guess will look exactly
   like a correct answer in the report.

The reference version is in `solution/.claude/agents/migration-validator.md`.
Write yours first, then diff -- the differences are the interesting part.
