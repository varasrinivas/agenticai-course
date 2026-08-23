# Oracle → PostgreSQL Migration Agent

Project context for Claude Code working in this directory.

## What this is

A five-phase migration system for a legacy Oracle UCC filing database. Source is **read-only**.
Cutover requires **human approval**. Neither of those is negotiable, and both are enforced in
`hooks.py` rather than by convention.

## Architecture

This is the **skills-first** build. Capstone 8 solves the same problem with five
subagents; here one context loads five skills on demand.

```
coordinator.py                five phases: discover -> schema -> data -> code -> validate
                              PHASE_SKILLS maps each phase to the skills it may load
  .claude/skills/*/SKILL.md   five rulebooks, each with references/ and scripts/
  .claude/settings.json       hook wiring -- identical to Capstone 8
  tools_oracle.py             MCP server `oracle_src`  -- READ ONLY
  tools_postgres.py           MCP server `pg_target`
  tools_local.py              write_artifact ONLY
  hooks.py                    three PreToolUse denials + the audit log
```

There is no `.claude/agents/`, and no `type_mapping.py`, `validation.py` or
`oracle_constructs.py` at the root. That logic lives inside the skills that explain it:

```
.claude/skills/
  oracle-pg-typing/          scripts/check_mapping.py      (was type_mapping.py)
  appsql-rewriting/          scripts/find_oracleisms.py    (was oracle_constructs.py,
                                                            and the scan_app_sql MCP tool)
  migration-validation/      scripts/compare_checksums.py  (was validation.py)
  nullability-preservation/  scripts/compare_nulls.py      loaded by TWO phases
  plsql-conversion/          references only -- borrows the scanner above
```

## Working on skills

- **`context: fork` is real, and this lab deliberately does not use it.** A forked skill spawns
  a subagent, so it gets its own context window and only its result comes back. Every skill here
  runs inline on purpose -- a single shared context is the architecture being measured. If you
  set `context: fork` on `migration-validation`, say so in the comparison: you have changed the
  experiment, not just the config.
- **An unrecognised frontmatter key is ignored silently**, so a typo leaves the skill behaving
  nothing like intended. `tests/test_skills_wellformed.py` validates against the real schema.
- **A skill that fails to load fails silently.** No error, no warning -- the agent just
  improvises. After changing skill wiring, check `migration_audit.jsonl` for an actual script
  execution before believing a green run.
- **Skill scripts must run standalone.** No project imports, no `config`. An agent that loads
  the skill has the file and nothing else.
- **`nullability-preservation` is shared by the `data` and `validate` phases on purpose.** If
  you find yourself copying its rule into a phase prompt, stop -- that duplication is exactly
  what this architecture exists to avoid.

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
