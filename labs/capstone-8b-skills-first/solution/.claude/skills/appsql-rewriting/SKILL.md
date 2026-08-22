---
name: appsql-rewriting
description: This skill should be used when finding and rewriting Oracle-specific SQL embedded in application source code — when asked to "scan the app for Oracle SQL", "rewrite these queries for PostgreSQL", "find Oracle-isms", or when working with .java, .py, or .sql application files that contain ROWNUM, NVL, DECODE, (+) joins, CONNECT BY, MERGE, or package calls. Produces unified diffs and never edits originals in place.
allowed-tools: [Read, Bash, Grep, Glob, mcp__migration_local__write_artifact]
---

# Rewriting Oracle SQL in application source

## Never edit an original

Application source is evidence. The diff is the deliverable, and it goes to a developer who
will apply it during their own release, not during your migration. Editing in place destroys
the thing they need to review against and puts your changes in a release you do not control.

Emit `artifacts/appsql/<filename>.diff` as a unified diff. Nothing else.

The `.claude/settings.json` in this project also denies `Edit(./app/**)` at the hook layer — so
if you try, the attempt is blocked and logged. Treat that as a backstop, not as the rule.

---

## Step 1 — Scan, do not grep by hand

```bash
python .claude/skills/appsql-rewriting/scripts/find_oracleisms.py --dir ../app
python .claude/skills/appsql-rewriting/scripts/find_oracleisms.py --file ../app/filing_repository.py
python .claude/skills/appsql-rewriting/scripts/find_oracleisms.py --dir ../app --json
```

The scanner reports file, line, construct, and whether it is translatable. Its regexes are the
same ones the PL/SQL converter uses, so the two phases cannot drift apart in what they consider
an Oracle-ism.

**The scanner finds candidates. You decide the rewrite.** A regex cannot tell you whether
`filed_date - TRUNC(SYSDATE)` meant whole days or elapsed time — only the surrounding code can.

Load `../plsql-conversion/references/construct-catalog.md` for what each construct becomes. It
is shared between the two skills deliberately: one catalog, two consumers.

---

## Step 2 — Rewrite, with the trap in mind

The three that matter most in this codebase:

**`ROWNUM` in `filing_repository.py`.** Check whether the original nests a subquery. If it does,
the intent was top-N *by the ordering*, and a bare `LIMIT` on the outer query reproduces it. If
it does not, the original was already returning arbitrary rows — say so in the diff comment
rather than silently "fixing" behaviour the application may depend on.

**`(+)` joins.** The `(+)` marks the nullable side. It goes on the **opposite** side from the
one you name in `LEFT JOIN`. Getting it backwards changes the row count and nothing errors.

**`MERGE` in `RiskReportDao.java`.** Needs a unique constraint to conflict on. Confirm one
exists in the generated DDL before emitting `ON CONFLICT` — otherwise the rewrite is valid SQL
that fails at runtime.

---

## Step 3 — The query whose bug is not in the SQL

`debtors_missing_address_line_2` in `filing_repository.py` is the one to slow down on:

```sql
SELECT ... FROM ucc_debtor WHERE mailing_address_2 IS NULL
```

That SQL is already valid PostgreSQL. It needs no rewrite at all — and it will still return the
wrong answer.

In Oracle, `mailing_address_2` is `NULL` for roughly 1,400 rows, because **Oracle stores the
empty string as NULL**. If the data load wrote those as zero-length strings instead, PostgreSQL
distinguishes `''` from `NULL` and the predicate matches ~0 rows. The query is correct; the
data underneath it is not.

**Say this in the diff comment.** A rewrite that silently leaves it alone is indistinguishable
from one that never looked at it, and this is the defect the whole capstone is built around.
See the `nullability-preservation` skill for the load-side fix.

---

## Output

One `artifacts/appsql/<filename>.diff` per source file that needed changes. For a file that
needed none, write nothing but list it in your summary as examined-and-clean — otherwise nobody
can tell the difference between "clean" and "not looked at".

Each diff carries a comment header naming: the constructs found, the rewrite chosen, and any
behaviour that changes as a result. A diff that changes behaviour without saying so is the one
that gets applied without review.
