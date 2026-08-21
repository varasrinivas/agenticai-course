---
name: appsql-rewriter
description: Finds Oracle-only SQL in application source and rewrites it for PostgreSQL as a unified diff. Use for phase 4 of the migration.
tools: mcp__migration_local__scan_app_sql, mcp__migration_local__write_artifact
model: claude-haiku-4-5-20251001
---

TODO: write this subagent's instructions.

It needs the full rewrite table and the note about predicates whose correctness depends on the load rather than the SQL.

Two things worth more than completeness here:

1. **Say why, not just what.** A mapping table the subagent can follow
   mechanically produces mechanical output. A table that explains what
   breaks when you get it wrong produces a subagent that notices the case
   you did not list.

2. **Say what to do when it is unsure.** A subagent with no instruction
   for uncertainty will guess, confidently, and the guess will look exactly
   like a correct answer in the report.

The reference version is in `solution/.claude/agents/appsql-rewriter.md`.
Write yours first, then diff -- the differences are the interesting part.
