---
description: Open the migration report and summarize what a human needs to decide
---

Read `artifacts/migration_report.json` and `artifacts/validation_summary.json`.

Produce a decision brief for the migration lead:

1. **Blockers** -- defects that must be fixed before cutover, each with the
   object name and what specifically is wrong.
2. **Manual-review queue** -- objects the specialists refused to convert,
   with the reason. `PKG_FILING_MAINT.log_audit` should be here; if it is
   not, the plsql-converter silently dropped an autonomous-transaction
   pragma and that is itself a blocker.
3. **Coverage** -- tables migrated, rows moved, PL/SQL objects converted
   vs queued, application files rewritten.
4. **Cost** -- token spend and estimated dollars.
5. **Recommendation** -- go or no-go, and what would have to change to
   turn a no-go into a go.

Do not run `pg_cutover`. Present the brief and stop.
