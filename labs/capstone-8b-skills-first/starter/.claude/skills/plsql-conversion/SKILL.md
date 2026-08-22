---
name: plsql-conversion
description: This skill should be used when converting Oracle PL/SQL to PostgreSQL PL/pgSQL — when asked to "convert a package", "migrate a trigger", "translate this procedure", "port PKG_*", or when PL/SQL source containing PRAGMA, CONNECT BY, BULK COLLECT, FORALL, or package specs needs a PostgreSQL equivalent. Defines the package-to-schema pattern and, critically, the constructs that must be refused rather than translated.
allowed-tools: [Read, Bash, mcp__oracle_src__oracle_get_plsql_source, mcp__pg_target__pg_apply_ddl, mcp__migration_local__write_artifact]
---

# PL/SQL → PL/pgSQL

## TODO(1) — Establish that refusal is a valid output

Most migration tooling treats "could not convert" as failure. This skill has to establish the
opposite, and it has to do it in the first few lines or the agent will not believe it later.

Write the argument. The strongest form of it is a claim about which converted objects actually
get re-read by a human. Work out what that claim is.

## TODO(2) — Wire in the scanner

`../appsql-rewriting/scripts/find_oracleisms.py` marks constructs that have no safe
translation. Tell the agent to run it **before** converting, and what to do when it reports one:

```bash
python .claude/skills/appsql-rewriting/scripts/find_oracleisms.py --file <source.sql> --refuse-only
```

Note that this script lives in a *different* skill. Say why that is correct rather than a
layering mistake — one catalog with two consumers, and what that prevents.

## TODO(3) — Packages → schemas

PostgreSQL has no packages. Write the conversion pattern.

Then work out the two things that do **not** survive it. One is about state; the other is about
what "private" means in each system. Both need recording rather than silently dropping.

Check the pattern against `app/RiskReportDao.java` — it calls a package. Does your pattern keep
that call site working unchanged? If not, reconsider it.

## TODO(4) — The refusal procedure

Run the scanner over `legacy-oracle/03_packages.sql` and find the construct it refuses. Then
write:

- what the construct does that PostgreSQL cannot do in-process
- the specific, observable failure if someone converts it anyway — say *when* it goes wrong
  and *why nobody notices*, not "it may not work"
- the three real alternatives, and why choosing between them is not a translation decision

Follow `references/refusal-template.md` for the output shape. That file is also a TODO.

## TODO(5) — Triggers

Oracle fuses the trigger body into the trigger; PostgreSQL splits it in two. Write that rule.

Then read `legacy-oracle/02_sequences_triggers.sql`. There are two `BEFORE INSERT` triggers on
`UCC_FILING` and they have **different fates**. Write the rule that sorts them, and be explicit
about what is lost if the agent treats them the same. One of them is business logic.

## TODO(6) — Output contract

State what the skill produces for a converted object and for a refused one, and what it means
if a run produces neither for some object.
