# Writing a refusal

A refusal is a deliverable. It is read by a database engineer who was not present for the
migration and who has to make an architecture decision from it. Judge it by one test:

> Could someone act on this without re-reading the original PL/SQL?

If not, it is not finished.

## What it must contain

1. **What the object does** — in business terms, not syntax terms
2. **The exact construct** that blocks conversion, quoted, with line numbers
3. **Why there is no mechanical equivalent** — the semantics that would be lost
4. **What silently breaks** if someone converts it anyway. Be specific about the failure mode
5. **The real options**, with the trade-off of each
6. **What the migration did instead** — so the gap is visible in the final report
7. **What depends on it** — the callers that are now broken or degraded

## Template

```markdown
# MANUAL REVIEW — <OBJECT_NAME>

**Status:** not converted
**Blocked by:** <CONSTRUCT>
**Source:** `<oracle object>`, lines <n>–<m>

## What it does
<Two or three sentences, in business terms.>

## Why it cannot be converted mechanically
<The semantics Oracle gives you and PostgreSQL does not.>

    <the offending lines, quoted verbatim>

## What breaks if you convert it anyway
<The specific, observable failure. Not "it may not work" — say what goes wrong,
 when, and why nobody notices.>

## Options
| Option | How it works | Cost |
|---|---|---|
| ... | ... | ... |

## Callers
<Who reaches this object, and what they get now.>

## What the migration did
<Left as-is / stubbed / partially converted.>
```

## Worked example — `PKG_FILING_MAINT.LOG_AUDIT`

The refusal this lab expects. Note that it names the failure mode concretely rather than
hedging, that the options table makes clear no option is free, and that it traces the callers —
the reviewer needs to know the blast radius, not just the blocker.

```markdown
# MANUAL REVIEW — PKG_FILING_MAINT.LOG_AUDIT

**Status:** not converted
**Blocked by:** PRAGMA AUTONOMOUS_TRANSACTION
**Source:** `legacy-oracle/03_packages.sql`, lines 116-124 (package body from 105)

## What it does
Writes one row to FILING_AUDIT recording an action taken against a filing.
It is called from lapse_expired_filings, which auto-lapses expired UCC
filings in a FORALL loop -- one audit row per lapsed filing.

## Why it cannot be converted mechanically
PRAGMA AUTONOMOUS_TRANSACTION runs the procedure in its own transaction, so
its COMMIT is independent of the caller's. PostgreSQL has no in-process
equivalent: a function always runs inside the caller's transaction.

    PROCEDURE log_audit (p_filing_id IN NUMBER,
                         p_action    IN VARCHAR2,
                         p_detail    IN VARCHAR2) IS
      PRAGMA AUTONOMOUS_TRANSACTION;
    BEGIN
      INSERT INTO filing_audit (audit_id, filing_id, action, detail)
      VALUES (seq_audit_id.NEXTVAL, p_filing_id, p_action, p_detail);
      COMMIT;
    END log_audit;

## What breaks if you convert it anyway
Deleting the pragma compiles and runs. Every audit row then joins the
caller's transaction, so if the nightly batch fails partway and rolls back,
the audit rows for the filings it had already lapsed disappear with it.

Nothing errors. No test fails. FILING_AUDIT still looks healthy, because the
successful runs are all there. What is missing is the record of the runs
that went wrong -- which is the only reason anyone opens an audit table.

## Options
| Option | How it works | Cost |
|---|---|---|
| `dblink` | Loopback connection, genuinely a separate transaction | Extension required; a connection per call; DB-side credentials |
| Background worker | Audit rows queued and written by a separate process | Audit lags the event; needs a durable queue or the row is lost on crash |
| Write from the application | Caller writes the audit row after its own commit | Lost if the process dies between the two; every caller must remember |

## Callers
- `pkg_filing_maint.lapse_expired_filings` (line 147), inside the FORALL loop
- reached in turn from `app/nightly_batch.sql` line 30

Converting lapse_expired_filings without resolving this leaves the nightly
batch running with no durable audit trail.

## What the migration did
Left unconverted. `pkg_filing_maint` was created as a schema and
`lapse_expired_filings` was converted, but it calls log_audit, so it will
fail at runtime until this is resolved. Flagged in the final report as
1 of 1 refusals.
```
