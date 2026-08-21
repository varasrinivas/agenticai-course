---
name: plsql-converter
description: Converts one PL/SQL package, procedure, function, or trigger to PL/pgSQL, or refuses and explains why. Use for phase 4 of the migration.
tools: mcp__oracle_src__oracle_get_plsql_source, mcp__pg_target__pg_apply_ddl, mcp__migration_local__write_artifact
model: claude-sonnet-4-6
---

TODO: write this subagent's instructions.

It needs the package-to-schema translation, the construct mapping table, and WHEN TO REFUSE.

Two things worth more than completeness here:

1. **Say why, not just what.** A mapping table the subagent can follow
   mechanically produces mechanical output. A table that explains what
   breaks when you get it wrong produces a subagent that notices the case
   you did not list.

2. **Say what to do when it is unsure.** A subagent with no instruction
   for uncertainty will guess, confidently, and the guess will look exactly
   like a correct answer in the report.

The reference version is in `solution/.claude/agents/plsql-converter.md`.
Write yours first, then diff -- the differences are the interesting part.
