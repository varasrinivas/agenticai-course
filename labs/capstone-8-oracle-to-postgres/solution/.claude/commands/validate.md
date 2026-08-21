---
description: Validate the migrated data against the Oracle source
argument-hint: "[table] optional, e.g. UCC_DEBTOR"
---

Validate the migration for $ARGUMENTS (blank means every table).

Run `python coordinator.py --phase validate`, then read
`artifacts/validation_summary.json`.

Report the defects FIRST, in full, before any pass count. Specifically
check `ucc_debtor.mailing_address_2`: Oracle reports roughly 1,400 NULLs
there. If PostgreSQL reports a non-zero empty-string count for the same
column, the load is defective and the migration is not ready, whatever
the overall pass rate says.

If the defect list is empty, verify the validator actually ran before
reporting success -- a validator that never executed and a clean bill of
health look identical in the JSON.
