# The Oracle construct catalog

TODO: one section per construct that `../appsql-rewriting/scripts/find_oracleisms.py`
detects. This file is the WHY behind each detection.

Lead with the constructs that must be REFUSED -- there are two, and putting them anywhere
but first buries them.

For each translatable construct give the Oracle form, the PostgreSQL form, and THE TRAP.
Several of these translate cleanly on paper and wrongly in practice:
  - one is assigned before ORDER BY, so the obvious rewrite changes the meaning
  - one marks the opposite side from the clause that replaces it
  - one treats NULL as matchable where its replacement does not
  - one returns a NUMBER in Oracle and an INTERVAL in PostgreSQL, and fails in production
    rather than at translation time
Find them by reading `app/` and `legacy-oracle/03_packages.sql`.

Finish with the group that is not SQL at all and must not be translated as statements.
