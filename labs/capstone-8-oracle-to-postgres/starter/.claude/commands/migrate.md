---
description: Run the Oracle to PostgreSQL migration (phases 1-5, stops before cutover)
argument-hint: "[phase] e.g. schema | data | code | validate, or blank for all"
---

Run the migration for $ARGUMENTS (blank means all five phases).

1. Confirm both containers are healthy:
   `docker compose ps` -- oracle must show `healthy`, not just `running`.
   Oracle Free takes 1-3 minutes to initialize on first boot.
2. If a phase was named, run `python coordinator.py --phase $ARGUMENTS`.
   Otherwise run `python coordinator.py --migrate-all`.
3. Watch for `[guard] DENY` lines in the output. Each one is a guardrail
   doing its job -- read the reason before assuming it is a bug.
4. When the run stops, report:
   - which phases completed
   - the manual-review queue (objects the specialists refused)
   - token spend against the budget
   - the path to `artifacts/migration_report.html`

Do not attempt cutover. That is `/validate` first, then a human.
