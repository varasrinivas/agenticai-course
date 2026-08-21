# Agent Specification — Legacy Migration System (Oracle → PostgreSQL)

> This is the **canonical agent-spec.md** for CAPSTONE-8. The lab's spec-driven section asks the
> student to read this spec, run `/generate-from-spec spec/agent-spec.md`, and diff the generated
> project against the hand-built `solution/`.

## 1. Business Context

Meridian Public Records must move an 11-state UCC filing system off Oracle onto PostgreSQL 16.
The system is a coordinator agent plus five specialist subagents that read the legacy Oracle
schema, generate PostgreSQL DDL, move the data, convert PL/SQL to PL/pgSQL, rewrite Oracle-only
SQL found in application source, and then *prove* the result is equivalent before any cutover.

The source database is **read-only**. Nothing the agent does may write to Oracle. Cutover requires
explicit human approval.

## 2. Agent Configuration

- Coordinator model: `claude-sonnet-4-6`
- Specialist models: `claude-sonnet-4-6` for `schema-translator` and `plsql-converter` (they do the
  hardest reasoning); `claude-haiku-4-5-20251001` for `data-migrator`, `appsql-rewriter`, and
  `migration-validator` (mechanical, high-volume)
- Framework: `claude-agent-sdk` (Python). Required imports: `query`, `tool`,
  `create_sdk_mcp_server`, `ClaudeAgentOptions`, `AssistantMessage`, `HookMatcher`,
  `PermissionResultAllow`, `PermissionResultDeny`
- Max turns per invocation: 20 (migration is genuinely long-running)
- Max output tokens: 8192 (DDL and PL/pgSQL bodies are large)
- Subagent context windows: isolated — a subagent sees only the object it was handed

## 3. System Prompt (coordinator)

You are the migration coordinator for an Oracle-to-PostgreSQL database migration. Work in five
phases, in order, and do not start a phase until the previous one has reported success:

1. **Discover** — call `oracle_describe_schema` once. Build an inventory of every table, sequence,
   trigger, view, materialized view, package, procedure, and function.
2. **Translate schema** — delegate each table to `schema-translator`. Collect the generated DDL and
   the type-mapping decision log.
3. **Move data** — delegate each table to `data-migrator`, largest first, so a failure surfaces
   early.
4. **Convert code** — delegate every PL/SQL object to `plsql-converter` and every application file
   to `appsql-rewriter`, in parallel.
5. **Validate** — delegate to `migration-validator`. Only after it reports may you propose
   `pg_cutover`.

Never call a database tool directly — always go through a specialist subagent. When a specialist
reports that an object cannot be converted automatically, put it on the manual-review queue with
the specific reason and continue; do not invent a translation you are not confident in. A
migration that reports 80% automated and 20% needing review is a success. A migration that reports
100% automated because you guessed is a failure.

## 4. Tools

### MCP server `oracle_src` (READ-ONLY)

| Tool | Parameters | Returns |
|---|---|---|
| `oracle_describe_schema` | `owner` (string, default `MERIDIAN`) | inventory of all objects with type, name, row count estimate |
| `oracle_get_ddl` | `object_type` (string), `object_name` (string) | `DBMS_METADATA.GET_DDL` output as text |
| `oracle_get_plsql_source` | `object_name` (string) | full `ALL_SOURCE` body for a package/procedure/function/trigger |
| `oracle_sample_rows` | `table_name` (string), `limit` (int, default 20) | sample rows as JSON, with Oracle type names preserved per column |
| `oracle_row_count` | `table_name` (string) | exact `COUNT(*)` |
| `oracle_checksum` | `table_name` (string), `columns` (string, comma-separated) | `SUM(ORA_HASH(...))` fingerprint plus per-column NULL counts |

### MCP server `pg_target`

| Tool | Parameters | Returns |
|---|---|---|
| `pg_apply_ddl` | `ddl` (string) | `{applied: bool, error: str|null}` |
| `pg_copy_load` | `table_name` (string), `csv_path` (string), `null_as` (string, default `\N`) | rows loaded |
| `pg_query` | `sql` (string) | result rows as JSON |
| `pg_row_count` | `table_name` (string) | exact `COUNT(*)` |
| `pg_checksum` | `table_name` (string), `columns` (string) | `sum(hashtext(...))` fingerprint plus per-column NULL and empty-string counts |
| `pg_cutover` | `confirm_token` (string) | flips `ucc_migrated` to `public` via `ALTER SCHEMA ... RENAME`. **HITL-gated.** |

### Local tools

| Tool | Parameters | Returns |
|---|---|---|
| `scan_app_sql` | `path` (string), `extensions` (string, default `.py,.java,.sql`) | list of `{file, line, snippet, oracle_constructs[]}` |
| `write_artifact` | `relative_path` (string), `content` (string) | absolute path written under `artifacts/` |

Every tool returns `{"content": [{"type": "text", "text": json.dumps(result)}]}`.

## 5. Subagents (declared as `.claude/agents/<name>.md`)

### schema-translator
- Description: Translates one Oracle table's DDL into PostgreSQL DDL and records a justified
  type-mapping decision for every column.
- Allowed tools: `oracle_get_ddl`, `oracle_sample_rows`, `write_artifact`
- Model: `claude-sonnet-4-6`
- Must emit, per column: Oracle type, chosen PostgreSQL type, and a one-line reason. Must map
  Oracle `DATE` to `timestamp(0)` and say why. Must convert sequence+trigger identity to
  `GENERATED BY DEFAULT AS IDENTITY` plus a `setval()`. Must not quote identifiers.

### data-migrator
- Description: Plans and executes a batched extract-and-load for one table.
- Allowed tools: `oracle_row_count`, `oracle_sample_rows`, `pg_copy_load`, `pg_query`,
  `write_artifact`
- Model: `claude-haiku-4-5-20251001`
- Batch size 10,000. Must set `null_as` explicitly so Oracle NULLs do not arrive as empty strings.
  Must handle `CLOB`/`BLOB` columns out-of-band rather than inline in CSV.

### plsql-converter
- Description: Converts one PL/SQL package, procedure, function, or trigger to PL/pgSQL.
- Allowed tools: `oracle_get_plsql_source`, `pg_apply_ddl`, `write_artifact`
- Model: `claude-sonnet-4-6`
- Packages become a schema plus functions. `PRAGMA AUTONOMOUS_TRANSACTION` has no safe equivalent —
  the subagent must refuse and queue it for manual review rather than silently dropping the pragma.

### appsql-rewriter
- Description: Finds Oracle-only SQL in application source and rewrites it for PostgreSQL.
- Allowed tools: `scan_app_sql`, `write_artifact`
- Model: `claude-haiku-4-5-20251001`
- Produces a unified diff per file. Never edits the original in place.

### migration-validator
- Description: Proves source and target are equivalent, or reports exactly where they are not.
- Allowed tools: `oracle_row_count`, `oracle_checksum`, `oracle_sample_rows`, `pg_row_count`,
  `pg_checksum`, `pg_query`, `write_artifact`
- Model: `claude-haiku-4-5-20251001`
- Runs six checks per table: row count, column checksum, NULL count per column, **empty-string
  count per column (PostgreSQL only — any non-zero value on a column that was NULL-only in Oracle
  is a defect)**, FK integrity, and a 20-row spot-check diff.

## 6. Hooks (declared in `.claude/settings.json`, implemented in `hooks.py`)

### PreToolUse — enforce Oracle read-only
- Matcher: `mcp__oracle_src__*`
- Behavior: parse the effective statement. Allow only `SELECT`, `WITH ... SELECT`,
  `DBMS_METADATA.GET_DDL`, and reads of `ALL_*`/`USER_*`/`DBA_*` dictionary views. Anything else
  returns `PermissionResultDeny(message="Source database is read-only: <stmt> rejected")`.

### PreToolUse — protect the PostgreSQL target
- Matcher: `mcp__pg_target__pg_apply_ddl`
- Behavior: deny `DROP DATABASE`, `DROP SCHEMA`, `DROP OWNED`, and any `CREATE`/`ALTER` whose
  target is not schema-qualified into `ucc_migrated`.

### PreToolUse (can_use_tool) — HITL cutover gate
- Matcher: `mcp__pg_target__pg_cutover`
- Behavior: always returns a denial carrying the current validation summary and the instruction to
  re-run with `--approve-cutover` after a human has read it. The agent can never approve itself.

### PostToolUse — audit log
- Matcher: `*`
- Behavior: append `{timestamp, tool_name, params, row_count, duration_ms}` to
  `migration_audit.jsonl`. Redact anything matching a DSN, `password=`, or `ORACLE_PWD`.

## 7. Guardrails

- Cost ceiling: abort the run if cumulative output tokens exceed 400,000.
- Circuit breaker: three consecutive subagent failures on the same phase halts the migration.
- Output validation: every generated DDL block is applied inside a transaction and rolled back
  first as a syntax check before being committed.

## 8. Sessions

Multi-turn via a `MigrationSession` helper that persists phase state to
`artifacts/session_state.json`, so a run interrupted after phase 3 resumes at phase 4 rather than
re-migrating. `fork()` produces a what-if branch for trying an alternative type mapping.

## 9. Deployment

- **Tier 1 (local, default)**: `docker compose up` — `gvenzl/oracle-free:23-slim` (source, seeded
  from `legacy-oracle/*.sql`), `postgres:16-alpine` (target), `agent` (the migration system).
  Oracle takes 1–3 minutes to initialize on first boot; the compose file gates the agent on its
  healthcheck.
- **Tier 2 (GCP)**: Cloud Run job, source over Cloud SQL Auth Proxy, target Cloud SQL for
  PostgreSQL.
- **Tier 3 (AWS)**: ECS task, target Aurora PostgreSQL, artifacts to S3.

## 10. Tests (pytest, in `tests/`)

- `test_type_mapping.py` — the `NUMBER`/`DATE`/`RAW`/`CLOB` mapping table is applied correctly
- `test_hooks_readonly.py` — `DROP TABLE`, `UPDATE`, `DELETE`, `TRUNCATE` against Oracle are all
  denied; `SELECT` is allowed
- `test_hooks_pg_guard.py` — `DROP SCHEMA public CASCADE` denied; `CREATE TABLE ucc_migrated.x`
  allowed
- `test_plsql_conversion.py` — `PKG_RISK_CALC` converts; the autonomous-transaction procedure is
  queued for manual review rather than converted
- `test_validator_catches_empty_string.py` — a deliberately bad load produces a non-zero
  empty-string divergence on `ucc_debtor.mailing_address_2`
- `test_cutover_hitl.py` — `pg_cutover` cannot succeed without the human approval flag

## 11. Evaluation Dataset (`evaluation/test_cases.json`, 20 scenarios)

1. Translate `UCC_FILING` → identity column, `timestamp(0)` dates, `text` collateral
2. Translate `UCC_SECURED_PARTY` → `RAW(16)` becomes `uuid`
3. Translate `STATE_SOS_SOURCE` → `TIMESTAMP WITH LOCAL TIME ZONE` becomes `timestamptz`
4. Translate `NUMBER` with no precision → `numeric`, with justification
5. Migrate 5,000 `UCC_FILING` rows → checksums match
6. Migrate `UCC_DEBTOR` → NULL counts match, empty-string count is zero
7. `FILED_DATE` of `2019-04-02 14:32:07` survives intact
8. Convert `PKG_RISK_CALC.score_debtor` → callable PL/pgSQL function
9. Convert the `BEFORE INSERT` sequence trigger → identity, no trigger emitted
10. Refuse to convert the autonomous-transaction audit procedure
11. Rewrite `ROWNUM <= 50` → `LIMIT 50`
12. Rewrite `NVL(a,b)` → `COALESCE(a,b)`
13. Rewrite `(+)` outer join → `LEFT JOIN`
14. Rewrite `CONNECT BY PRIOR` amendment walk → `WITH RECURSIVE`, same tree
15. Rewrite `DECODE` → `CASE`
16. Rewrite `MERGE` → `INSERT ... ON CONFLICT`
17. Deny `DROP TABLE UCC_FILING` against Oracle
18. Deny `DROP SCHEMA public CASCADE` against PostgreSQL
19. Block `pg_cutover` pending human approval
20. Detect the planted `mailing_address_2` empty-string divergence

Pass threshold: 18 of 20.

## 12. File Structure

```
generated/
├── CLAUDE.md
├── .claude/
│   ├── agents/{schema-translator,data-migrator,plsql-converter,appsql-rewriter,migration-validator}.md
│   ├── commands/{migrate,validate,report}.md
│   └── settings.json
├── coordinator.py
├── tools_oracle.py
├── tools_postgres.py
├── tools_local.py
├── hooks.py
├── config.py
├── report.py
├── session.py
├── observability/{tracer.py,metrics.py}
├── evaluation/{test_suite.py,test_cases.json}
├── tests/
├── artifacts/            (created at runtime: DDL, diffs, session_state.json)
├── migration_audit.jsonl (created at runtime)
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

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

## How students use this spec

1. Read this spec alongside `solution/` — the solution is the reference, not the destination.
2. Run `/generate-from-spec spec/agent-spec.md`, writing into `generated/`.
3. Diff `generated/` against `solution/`. Where they differ, decide which is right and why.
4. Iterate: add a sixth subagent (`performance-advisor`) to *the spec*, regenerate, and watch the
   whole project absorb it without you editing six files by hand.
