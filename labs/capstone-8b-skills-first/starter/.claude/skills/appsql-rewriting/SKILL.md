---
name: appsql-rewriting
description: This skill should be used when finding and rewriting Oracle-specific SQL embedded in application source code — when asked to "scan the app for Oracle SQL", "rewrite these queries for PostgreSQL", "find Oracle-isms", or when working with .java, .py, or .sql application files that contain ROWNUM, NVL, DECODE, (+) joins, CONNECT BY, MERGE, or package calls. Produces unified diffs and never edits originals in place.
allowed-tools: [Read, Bash, Grep, Glob, mcp__migration_local__write_artifact]
---

# Rewriting Oracle SQL in application source

## TODO(1) — The never-edit-in-place rule

Write the rule and, more importantly, the reason. It is not about tidiness — it is about who
applies the change and when. Think about whose release the diff lands in.

Note that `.claude/settings.json` also denies `Edit(./app/**)` at the hook layer. Explain the
relationship between the two: which is the rule and which is the backstop, and why you want
both.

## TODO(2) — Wire in the scanner

`scripts/find_oracleisms.py` is a TODO in this directory. Once it works:

```bash
python .claude/skills/appsql-rewriting/scripts/find_oracleisms.py --dir ../app
```

Write the instruction that tells the agent where the scanner's authority ends. A regex can find
`ROWNUM`; it cannot decide what the rewrite should be. Draw that line explicitly, with an
example from this codebase where the surrounding code changes the answer.

## TODO(3) — The three that matter here

Run the scanner over `../app` and pick the constructs that carry real risk in *this* codebase,
not in general. For each, write what the agent must check before committing to a rewrite.

Two hints, because these are the ones that get silently mistranslated:

- one of them involves which side of a join the operator marks, and getting it backwards
  changes the row count without erroring
- one of them needs something to exist in the generated DDL before the rewrite is even valid,
  so the agent has to go and look

## TODO(4) — The query whose bug is not in the SQL

Find `debtors_missing_address_line_2` in `app/filing_repository.py`.

That query is already valid PostgreSQL. It needs no rewrite. It will still return the wrong
answer. Write the explanation, and say what the agent must put in the diff comment.

Then work out why "leave it alone" and "never looked at it" produce identical output, and write
the instruction that distinguishes them. Cross-reference the `nullability-preservation` skill
for the actual fix — this skill describes the symptom, that one owns the cure.

## TODO(5) — Output contract

One diff per file that needed changes. Decide what happens for a file that needed none — and
note that "write nothing" makes clean files indistinguishable from unexamined ones. Write the
rule that closes that gap.

State what each diff's comment header must carry. A diff that changes behaviour without saying
so is the one that gets applied without review.
