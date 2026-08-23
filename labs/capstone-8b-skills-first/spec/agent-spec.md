# Agent Specification — Legacy Migration System, Skills-First (Oracle → PostgreSQL)

> This is the **canonical agent-spec.md** for CAPSTONE-8B. The lab's spec-driven section asks the
> student to read this spec, run `/generate-from-spec spec/agent-spec.md`, and diff the generated
> project against the hand-built `solution/`.
>
> **Read this next to `labs/capstone-8-oracle-to-postgres/spec/agent-spec.md`.** The two specs
> describe the same system solved two ways. Sections 1, 4 (local tools), 5 and 12 differ. Sections
> 6–11 are near-identical, and that is itself the finding: guardrails, sessions, deployment, tests
> and the evaluation set are **orthogonal** to the skills-vs-subagents choice.

## 1. Business Context

Meridian Public Records must move an 11-state UCC filing system off Oracle onto PostgreSQL 16.
The system reads the legacy Oracle schema, generates PostgreSQL DDL, moves the data, converts
PL/SQL to PL/pgSQL, rewrites Oracle-only SQL found in application source, and then *proves* the
result is equivalent before any cutover.

The source database is **read-only**. Nothing the agent does may write to Oracle. Cutover requires
explicit human approval.

**What differs from Capstone 8:** there are no subagents. One coordinator context runs all five
phases, loading skills on demand. The specialist knowledge that lived in five subagent prompts
lives in five skills, each shipping its own references and executable checkers.

The deliverable therefore includes one artifact Capstone 8 does not produce:
`evaluation/architecture_comparison.md`, a measured comparison of the two architectures on the
same problem. **A comparison that flatters this architecture is a failed deliverable.**

## 2. Agent Configuration

- Coordinator model: `claude-sonnet-4-6`
- **No per-specialist model routing.** Capstone 8 routed hard reasoning to Sonnet and mechanical
  work to Haiku, per subagent. A single context cannot do that — this is a real cost the
  comparison must quantify, not a detail to gloss.
- Framework: `claude-agent-sdk` (Python). Required imports: `query`, `tool`,
  `create_sdk_mcp_server`, `ClaudeAgentOptions`, `AssistantMessage`, `HookMatcher`,
  `PermissionResultAllow`, `PermissionResultDeny`
- Max turns per invocation: 20
- Max output tokens: 8192
- **Context: shared.** Every phase appends to the same conversation. Phase 5 has seen phases 2–4.

### Skill discovery — two options, both required

```python
ClaudeAgentOptions(
    ...,
    setting_sources=["project"],   # without this, .claude/skills/ is never read
    skills=PHASE_SKILLS[phase],    # per-phase allowlist
)
```

`setting_sources` accepts `"user"`, `"project"`, `"local"`. `skills` accepts a list of names or
the literal `"all"`.

**Omit either and nothing errors.** No warning, no missing-skill message — the agent improvises
the type mapping from memory and produces a migration that looks fine. Verify from
`migration_audit.jsonl` that a bundled script actually ran before trusting any run.

Do **not** pass `skills="all"`: it makes every skill available in every phase and discards the
scoping in §5.

## 3. System Prompt (coordinator)

You are the migration coordinator for an Oracle-to-PostgreSQL database migration. Work in five
phases, in order, and do not start a phase until the previous one has reported success:

1. **Discover** — call `oracle_describe_schema` once. Build an inventory of every table, sequence,
   trigger, view, materialized view, package, procedure, and function.
2. **Translate schema** — one table at a time. The `oracle-pg-typing` skill carries the mapping
   rules and a deterministic checker.
3. **Move data** — one table at a time, largest first, so a failure surfaces early.
4. **Convert code** — every PL/SQL object, then the application source.
5. **Validate** — all six checks, every table. Only after it reports may you propose `pg_cutover`.

Skills are not documentation you may consult if you feel like it — they are the procedure. When a
skill bundles a script that computes an answer you could also reason out, **run the script**: it
is faster, consistent on a bad day, and unit-tested.

When an object cannot be converted automatically, put it on the manual-review queue with the
specific reason and continue; do not invent a translation you are not confident in. A migration
that reports 80% automated and 20% needing review is a success. One that reports 100% because you
guessed is a failure.

In phase 5 you are auditing your own work from phases 2–4. Re-derive every number from the
database. Do not report a count you remember writing.

You cannot approve your own cutover.

## 4. Tools

### MCP server `oracle_src` (READ-ONLY)

Identical to Capstone 8.

| Tool | Parameters | Returns |
|---|---|---|
| `oracle_describe_schema` | `owner` (string, default `MERIDIAN`) | inventory of all objects with type, name, row count estimate |
| `oracle_get_ddl` | `object_type` (string), `object_name` (string) | `DBMS_METADATA.GET_DDL` output as text |
| `oracle_get_plsql_source` | `object_name` (string) | full `ALL_SOURCE` body |
| `oracle_sample_rows` | `table_name` (string), `limit` (int, default 20) | sample rows as JSON, Oracle type names preserved |
| `oracle_row_count` | `table_name` (string) | exact `COUNT(*)` |
| `oracle_checksum` | `table_name` (string), `columns` (string) | `SUM(ORA_HASH(...))` plus per-column NULL counts |

### MCP server `pg_target`

Identical to Capstone 8.

| Tool | Parameters | Returns |
|---|---|---|
| `pg_apply_ddl` | `ddl` (string) | `{applied: bool, error: str|null}` |
| `pg_copy_load` | `table_name`, `csv_path`, `null_as` (string, default `\N`) | rows loaded |
| `pg_query` | `sql` (string) | result rows as JSON |
| `pg_row_count` | `table_name` (string) | exact `COUNT(*)` |
| `pg_checksum` | `table_name`, `columns` | `sum(hashtext(...))` plus per-column NULL and empty-string counts |
| `pg_cutover` | `confirm_token` (string) | flips `ucc_migrated` to `public`. **HITL-gated.** |

### MCP server `migration_local` — **one tool, not two**

| Tool | Parameters | Returns |
|---|---|---|
| `write_artifact` | `relative_path` (string), `content` (string) | path written under `artifacts/` |

**`scan_app_sql` is deliberately absent.** In Capstone 8 it was an MCP tool here; in 8B the same
regex ships as `.claude/skills/appsql-rewriting/scripts/find_oracleisms.py` and the agent runs it
with Bash.

The distinction the spec is drawing:

- An **MCP tool** is described in every request's tool list whether or not the phase needs it, and
  its rationale lives somewhere with no link back to it.
- A **skill script** loads only with its skill, and sits beside the `SKILL.md` explaining when to
  run it and how to read the output.

`write_artifact` stays a tool because it is a *capability*, not knowledge: it enforces the
`artifacts/` confinement boundary, which must hold in every phase regardless of which skills are
loaded.

Every tool returns `{"content": [{"type": "text", "text": json.dumps(result)}]}`.

## 5. Skills (declared as `.claude/skills/<name>/SKILL.md`)

Frontmatter follows Claude Code's schema. **`name` and `description` are required.** Optional and
relevant here: `model`, `allowed-tools`, `disallowed-tools`, `user-invocable`,
`disable-model-invocation`, `argument-hint`, `effort`, `shell`, plus the skill-only
`when_to_use`, `paths`, `hooks`, `context`, `agent` and `background`. `name` must match the
directory.

> **`context` decides where the skill runs**: `inline` (the default) expands it into the current
> conversation; `fork` spawns a subagent, giving the skill its own context window with only its
> result returned. `agent` picks the agent type for a fork; `background` makes the fork report
> back as a task notification instead of blocking.
>
> **Every skill in this lab runs inline, deliberately** -- one shared context is the thing being
> measured against Capstone 8. `context: fork` is the obvious lever to reach for in §3's
> validator problem, and reaching for it changes the experiment rather than tuning it.
>
> An unrecognised key is ignored silently rather than rejected, so a typo behaves like an
> absent field. `tests/test_skills_wellformed.py` validates against the real schema.

Bundled resources follow the standard layout: `scripts/` for executables, `references/` for
material loaded on demand, `assets/` for files used in output.

### oracle-pg-typing
- Description trigger phrases: "translate a table", "generate DDL", "map this column", any Oracle
  type name
- Allowed tools: `oracle_get_ddl`, `oracle_sample_rows`, `pg_apply_ddl`, `write_artifact`, `Read`, `Bash`
- References: `type-matrix.md` (full matrix), `number-precision.md` (`NUMBER(p,s)` bands)
- Scripts: `check_mapping.py` — returns target type, reason, and a confidence of
  `confident` / `check_data` / `manual`
- Core rule: the DDL declares, the rows hold — two reads per table, never one. `DATE` →
  `timestamp(0)`, never `date`. Lowercase identifiers, never quoted. Sequence+trigger identity →
  `GENERATED BY DEFAULT AS IDENTITY` plus a `setval` after load, **without** deleting the second
  `BEFORE INSERT` trigger, which is business logic.

### plsql-conversion
- Description trigger phrases: "convert a package", "migrate a trigger", `PRAGMA`, `CONNECT BY`,
  `BULK COLLECT`
- Allowed tools: `oracle_get_plsql_source`, `pg_apply_ddl`, `write_artifact`, `Read`, `Bash`
- References: `construct-catalog.md`, `refusal-template.md`
- Scripts: none of its own — calls `../appsql-rewriting/scripts/find_oracleisms.py`. **One catalog,
  two consumers**, so the scanner and the converter cannot disagree about what counts as an
  Oracle-ism.
- Core rule: packages become schemas of the same name. `PRAGMA AUTONOMOUS_TRANSACTION` in
  `PKG_FILING_MAINT.log_audit` must be **refused**, not converted.

### appsql-rewriting
- Description trigger phrases: "scan the app for Oracle SQL", "find Oracle-isms", "rewrite these
  queries"
- Allowed tools: `write_artifact`, `Read`, `Bash`, `Grep`, `Glob`
- Scripts: `find_oracleisms.py` — the construct registry plus a line-level scanner
- Core rule: never edit an original; emit a unified diff. `debtors_missing_address_line_2` needs
  **no** rewrite and is still wrong — the diff comment must say why.

### nullability-preservation
- Description trigger phrases: "load a table", "run pg_copy_load", "compare NULL counts"
- Allowed tools: `oracle_row_count`, `oracle_sample_rows`, `pg_copy_load`, `pg_query`,
  `pg_row_count`, `write_artifact`, `Read`, `Bash`
- Scripts: `compare_nulls.py`
- **Loaded by two phases** — `data` and `validate`. This is the architecture's headline claim made
  structural: in Capstone 8 the same knowledge was copy-pasted into two subagent prompts and the
  copies were free to drift. Here the loader and the validator read one file.
  `tests/test_skills_wellformed.py` asserts this sharing.
- Core rule: `oracle_nulls == pg_nulls` **and** `pg_empty_strings == 0`. Oracle has no empty
  string, so the second half is a one-sided assertion, not a comparison.

### migration-validation
- Description trigger phrases: "validate the migration", "reconcile the tables", "run the six checks"
- Allowed tools: `oracle_row_count`, `oracle_checksum`, `oracle_sample_rows`, `pg_row_count`,
  `pg_checksum`, `pg_query`, `write_artifact`, `Read`, `Bash`
- References: `check-catalog.md`
- Scripts: `compare_checksums.py` — aggregates plus the spot-check and its DATE-truncation detector
- Core rule: six checks per table — row count, column checksum, NULL count, **empty-string count
  (PostgreSQL only)**, FK integrity, 20-row spot-check diff. Checks 1 and 2 pass on a broken
  migration; check 6 is the only one that sees `DATE` truncation. Two severities: BLOCKER (the
  migration caused it) and WARNING (present in Oracle too). **Never emit a percentage.**

### Phase → skill map (`coordinator.PHASE_SKILLS`)

The skills-first analogue of a subagent's `tools:` frontmatter — a phase cannot reach knowledge it
has no business using.

| Phase | Skills loaded |
|---|---|
| discover | *(none — inventory needs no rulebook)* |
| schema | `oracle-pg-typing` |
| data | `nullability-preservation` |
| code | `plsql-conversion`, `appsql-rewriting` |
| validate | `migration-validation`, `nullability-preservation` |
| cutover | *(none)* |

The load phase deliberately cannot load `migration-validation`: it must not be able to mark its
own work correct.

## 6. Hooks

**Unchanged from Capstone 8, and that is the point** — guardrails sit between the agent and the
tools, so they are unaffected by how the agent's knowledge is organised. `hooks.py`,
`hooks_cli.py` and `.claude/settings.json` are byte-identical across the two labs; `diff` them
and see. An architecture rewrite that touches none of the safety layer is the finding.

- **PreToolUse — Oracle read-only.** Matcher `mcp__oracle_src__*`. Allow-list: `SELECT`,
  `WITH ... SELECT`, `DBMS_METADATA.GET_DDL`, `ALL_*`/`USER_*`/`DBA_*` reads. Everything else
  returns `PermissionResultDeny`.
- **PreToolUse — protect the target.** Matcher `mcp__pg_target__pg_apply_ddl`. Deny `DROP
  DATABASE`/`SCHEMA`/`OWNED`, and any `CREATE`/`ALTER` not qualified into `ucc_migrated`.
- **PreToolUse (`can_use_tool`) — HITL cutover gate.** Matcher `mcp__pg_target__pg_cutover`.
  Always denies, carrying the current validation summary. Only `--approve-cutover` opens it, via
  an environment variable this process reads and cannot write.
- **PostToolUse — audit log.** Matcher `*`. Appends
  `{timestamp, tool_name, params, row_count, duration_ms}` to `migration_audit.jsonl`, with DSNs,
  `password=` and `ORACLE_PWD` redacted.

## 7. Guardrails

- Cost ceiling: abort if cumulative output tokens exceed 400,000.
- Circuit breaker: three consecutive failures on the same phase halts the migration.
- Output validation: every generated DDL block is applied in a transaction and rolled back first
  as a syntax check.

## 8. Sessions

`MigrationSession` persists phase state to `artifacts/session_state.json`, so a run interrupted
after phase 3 resumes at phase 4.

Note the interaction with a shared context: resuming phase 4 in a **new** process gives it none of
phases 2–3's conversation. The session file carries the state; the context does not. Under
subagents this distinction barely mattered. Here it changes what phase 5 has seen — and therefore
how independent its validation is. Worth recording in the comparison.

## 9. Deployment

Unchanged from Capstone 8.

- **Tier 1 (local, default)**: `docker compose up` — `gvenzl/oracle-free:23-slim` (source, seeded
  from `legacy-oracle/*.sql`), `postgres:16-alpine` (target), `agent`. Oracle takes 1–3 minutes on
  first boot; the compose file gates the agent on its healthcheck.
- **Tier 2 (GCP)**: Cloud Run job, Cloud SQL for PostgreSQL target.
- **Tier 3 (AWS)**: ECS task, Aurora PostgreSQL target, artifacts to S3.

## 10. Tests (pytest, in `tests/`)

Carried over from Capstone 8, re-pointed at the skill scripts, plus one new file.

- **`test_skills_wellformed.py` (new)** — frontmatter parses; `name` matches directory;
  `description` carries trigger phrases; `allowed-tools` names only tools this project provides;
  **no invented frontmatter keys**; every bundled script imports, passes its own `--self-test`, and
  runs standalone with an empty `PYTHONPATH`; every referenced file exists; `PHASE_SKILLS` names
  only real skills and every skill is used; `nullability-preservation` is shared by exactly the
  `data` and `validate` phases.

  This test exists because a skill Claude Code declines to load **fails silently** — the agent does
  not error, it improvises. There is no runtime signal, so the contract is asserted at build time.

- `test_type_mapping.py` — imports `map_type` from `oracle-pg-typing/scripts/check_mapping.py`
- `test_plsql_conversion.py` — imports the registry from `appsql-rewriting/scripts/find_oracleisms.py`
- `test_validator_catches_empty_string.py` — exercises `compare_checksums.py` and `compare_nulls.py`,
  and asserts the two agree on what a correct load looks like
- `test_hooks_readonly.py`, `test_hooks_pg_guard.py`, `test_cutover_hitl.py` — unchanged

Scripts are loaded **by path** (`conftest.load_skill_script`), not by package import:
`.claude/skills/*/scripts/` is deliberately off `sys.path`, because a skill script must be
runnable by an agent holding nothing but the file.

**Two bugs found while building this lab.** Both originated in Capstone 8 and have since been fixed there too, so the two labs agree again:

1. The conftest fixture `audit_log` shadowed the `hooks.audit_log` function the tests import,
   so three tests awaited a `Path` object. Renamed to `audit_log_path`.
2. `audit_log` redacted the *serialized JSON* of the tool input. The greedy match that catches a
   secret also eats the closing `"` and `}`, so `json.loads` raised — inside a PostToolUse hook, on
   precisely the calls carrying credentials. Replaced with `redact_structure`, which redacts string
   values in place and cannot corrupt the document.

## 11. Evaluation Dataset (`evaluation/test_cases.json`, 20 scenarios)

**Identical to Capstone 8** — that is what makes the two scores comparable. Pass threshold 18/20.

Plus `evaluation/architecture_comparison.md`, which is scored on honesty rather than on the
numbers being favourable.

## 12. File Structure

```
generated/
├── CLAUDE.md
├── .claude/
│   ├── skills/
│   │   ├── oracle-pg-typing/{SKILL.md,references/{type-matrix,number-precision}.md,scripts/check_mapping.py}
│   │   ├── plsql-conversion/{SKILL.md,references/{construct-catalog,refusal-template}.md}
│   │   ├── appsql-rewriting/{SKILL.md,scripts/find_oracleisms.py}
│   │   ├── nullability-preservation/{SKILL.md,scripts/compare_nulls.py}
│   │   └── migration-validation/{SKILL.md,references/check-catalog.md,scripts/compare_checksums.py}
│   ├── commands/{migrate,validate,report}.md
│   └── settings.json          (identical to Capstone 8)
│                              NO agents/ directory
├── coordinator.py             (single context; PHASE_SKILLS map)
├── tools_oracle.py
├── tools_postgres.py
├── tools_local.py             (write_artifact only)
├── hooks.py
├── config.py
├── report.py
├── session.py
├── observability/{tracer.py,metrics.py}
├── evaluation/{test_suite.py,test_cases.json,architecture_comparison.md}
├── tests/
├── artifacts/                 (runtime: DDL, diffs, session_state.json)
├── migration_audit.jsonl      (runtime)
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

There is **no `type_mapping.py`, `oracle_constructs.py` or `validation.py` at the project root**.
That logic moved into the skills that explain it. Finding those files in `generated/` means the
generator produced the Capstone 8 shape.

## Acceptance Criteria

- All Python files import from `claude_agent_sdk` only — no `client.messages.create()` anywhere
  outside `appendix/manual-loop.py`
- `pytest tests/ -v` passes 100%
- `python evaluation/test_suite.py` scores ≥ 18/20
- `docker compose up` brings up both databases and the agent completes phases 1–5 unattended,
  then **stops** at the cutover gate
- Every row of `UCC_DEBTOR` that was NULL in Oracle is NULL — not empty string — in PostgreSQL
- `migration_audit.jsonl` has one entry per tool call, with no credentials in it
- Attempting any write against Oracle is denied and logged
- **`ClaudeAgentOptions` passes `setting_sources` and a per-phase `skills` list** — and the audit
  log proves a bundled script actually ran
- **`evaluation/architecture_comparison.md` is filled in from a real run**, including the
  validator-independence trials, and reports an unfavourable result if that is what happened

## How students use this spec

1. Read this spec alongside `solution/` — the solution is the reference, not the destination.
2. Read it alongside **Capstone 8's spec**. Diff §5 and §12. Everything else being nearly identical
   is the lesson.
3. Run `/generate-from-spec spec/agent-spec.md`, writing into `generated/`.
4. Diff `generated/` against `solution/`. Where they differ, decide which is right and why.
5. Iterate: add a sixth skill (`index-strategy`) to *the spec*, regenerate, and watch the project
   absorb it. Then add the same capability to Capstone 8's spec as a sixth subagent and compare
   what each change cost.
