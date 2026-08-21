# Oracle → PostgreSQL Migration Agent

Project context for Claude Code working in this directory.

## What this is

A five-phase migration system for a legacy Oracle UCC filing database. Source is **read-only**.
Cutover requires **human approval**. Neither of those is negotiable, and both are enforced in
`hooks.py` rather than by convention.

## Architecture

```
coordinator.py           five phases: discover -> schema -> data -> code -> validate
  .claude/agents/*.md    five specialists; the coordinator never calls a DB tool directly
  tools_oracle.py        MCP server `oracle_src`  -- READ ONLY
  tools_postgres.py      MCP server `pg_target`
  tools_local.py         scan_app_sql, write_artifact
  hooks.py               three PreToolUse denials + the audit log
  type_mapping.py        the Oracle->PostgreSQL type table, as testable code
  validation.py          reconciliation arithmetic
  oracle_constructs.py   the registry of constructs that do not survive the move
```

## Rules for working in this repo

- **Never write to Oracle.** Not in code, not in a script, not "just to test". The hook denies
  it, the grant denies it, and if you find a way around both, that is a bug to report rather than
  a technique to use.
- **Never create PostgreSQL objects outside `ucc_migrated`.** Cutover is one atomic
  `ALTER SCHEMA ... RENAME`; a single object in `public` breaks it.
- **Never set `CUTOVER_APPROVED`.** Only a human passing `--approve-cutover` does that.
- **Do not edit `../legacy-oracle/` or `../app/`.** Those are the fixtures the exercise is built
  on. The rewriter emits diffs into `artifacts/`; it does not edit sources in place.
- This is **SDK Tier 3**: `claude_agent_sdk` only. No `client.messages.create()` outside
  `../appendix/manual-loop.py`, which is labelled as a teaching artifact.

## The type mapping rule people get wrong

Oracle `DATE` maps to `timestamp(0)`, **not** `date`. Oracle DATE carries a time component.
Mapping it to `date` compiles, loads, and silently truncates `14:32:07` to midnight — which
changes which filings appear to have lapsed. Nothing errors.

## The data rule people get wrong

Oracle stores the empty string as NULL. PostgreSQL does not. Always pass `null_as` explicitly to
`pg_copy_load`. Get this wrong and ~1,400 `ucc_debtor.mailing_address_2` NULLs become empty
strings, every `IS NULL` predicate downstream stops matching them, and no constraint or row count
notices.

## When to refuse rather than translate

`PRAGMA AUTONOMOUS_TRANSACTION` has no safe PostgreSQL equivalent. Do not drop the pragma and
emit the rest — that runs, and it inverts the semantics so audit rows vanish on exactly the
rollbacks they exist to survive. Queue it for manual review with the three redesign options.

More generally: a refusal with a reason is a useful output. A confident wrong translation is not,
because it passes review.

## Commands

```bash
docker compose up -d oracle postgres          # wait for oracle to read "healthy"
python coordinator.py --migrate-all           # phases 1-5, stops at the gate
python coordinator.py --phase schema          # one phase
python coordinator.py --migrate-all --resume  # skip completed phases
pytest tests/ -v                              # no DB or API key needed
python evaluation/test_suite.py               # 20 scenarios, threshold 18
```

Slash commands: `/migrate`, `/validate`, `/report`.

## Reading the output

- `artifacts/migration_report.html` — the human-facing decision brief; defects first
- `artifacts/validation_summary.json` — machine-readable; `cutover_recommended` is the field
  that matters
- `migration_audit.jsonl` — one line per tool call, credentials redacted
- `artifacts/ddl/`, `artifacts/plsql/`, `artifacts/appsql/` — generated output and diffs
- `*.MANUAL_REVIEW.md` — things a specialist correctly refused
