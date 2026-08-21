# Capstone 8: Legacy Migration Agent — Oracle → PostgreSQL

## What You'll Build

A coordinator agent plus five specialist subagents that migrate a legacy Oracle UCC filing
system to PostgreSQL 16 — schema, data, PL/SQL, and application SQL — running against two live
containers, and then *prove* the result is correct before any cutover.

```
migration-coordinator  (claude-sonnet-4-6)
  |
  |-- schema-translator     Oracle DDL  ->  PostgreSQL DDL + type-mapping decision log
  |-- data-migrator         batched extract -> COPY load; LOB, DATE and encoding handling
  |-- plsql-converter       packages / procedures / functions / triggers -> PL/pgSQL
  |-- appsql-rewriter       scans app/ source, rewrites Oracle-only SQL
  |-- migration-validator   row counts, checksums, NULL-vs-empty diffs, FK, spot checks
  |
  +-- HUMAN APPROVAL GATE ---> pg_cutover
```

**Difficulty: 5/5 (6–8 hours)** · **SDK Tier 3** (`claude-agent-sdk`, spec-driven)

## Prerequisites

- **Modules**: M07 (MCP), M13–M14 (planning, multi-agent), M15B (build lab), M16–M18
  (guardrails, HITL, evaluation), M22B (deploy)
- Python 3.10+
- Docker Desktop with **~6 GB free disk** and **6 GB RAM allocated**
- An `ANTHROPIC_API_KEY`

> **Using Rancher Desktop instead of Docker?** If you chose the dockerd runtime, every command
> below works as-is. If you chose containerd, replace `docker` with `nerdctl`. See
> `prompts/10-rancher-deployment.md`.

### Before you start: the Oracle container

This lab runs a **real Oracle database**, not a mock. That buys you a migration you can actually
believe, and it costs you three things worth knowing up front:

| | |
|---|---|
| **Image size** | `gvenzl/oracle-free:23-slim` is ~2.5 GB pulled, ~4 GB on disk once initialized |
| **First boot** | 1–3 minutes while Oracle creates the pluggable database and runs the seed scripts. `docker compose` gates the agent on the healthcheck, so you do not have to guess. |
| **Apple Silicon / ARM** | Oracle publishes x86_64 only. The compose file sets `platform: linux/amd64` and it runs under emulation — correctly, but slowly. |

**If you cannot run Oracle**, use the fixtures profile:

```bash
docker compose --profile fixtures up
```

The `oracle_*` tools then replay canned responses from `legacy-oracle/fixtures/`. Phases 1, 2, 4
and 5 all work; phase 3 reports that it cannot move real rows. You still build and exercise every
guardrail, the type mapping, the PL/SQL refusal, and the validator.

## Setup

```bash
cd labs/capstone-8-oracle-to-postgres

# 1. Credentials
cp starter/.env.example starter/.env
# edit starter/.env and add your ANTHROPIC_API_KEY

# 2. Dependencies (for running tests locally, outside the container)
pip install -r requirements.txt

# 3. Bring up both databases
cd starter
docker compose up -d oracle postgres

# 4. Wait for Oracle. This is the step people skip.
docker compose ps
# oracle must read "healthy", not just "running". Watch it with:
docker compose logs -f oracle
# You are waiting for: DATABASE IS READY TO USE!

# 5. Confirm the legacy schema seeded
docker compose exec oracle sqlplus -S migration_reader/'ReadOnly#2026'@FREEPDB1 \
  <<< "select count(*) from meridian.ucc_filing;"
# Expect: 5000
```

## The Legacy Schema

Six tables, two packages, three views, one materialized view. Every object contains at least one
thing that does not translate cleanly — that is why it is there.

| Object | Rows | The trap it plants |
|---|---:|---|
| `UCC_FILING` | 5,000 | Sequence + trigger identity; `FILED_DATE`/`LAPSE_DATE` are Oracle `DATE` (time component); `COLLATERAL_DESC` is a `CLOB` |
| `UCC_DEBTOR` | 7,418 | `MAILING_ADDRESS_2` holds the empty string for ~1,400 rows — **the planted bug** |
| `UCC_SECURED_PARTY` | 5,000 | `TAX_ID RAW(16)`; `VARCHAR2(n BYTE)` vs `CHAR` semantics |
| `UCC_AMENDMENT` | 1,251 | Self-referencing parent, walked with `CONNECT BY PRIOR` |
| `FILING_AUDIT` | 385 | `BLOB` column; written by an autonomous-transaction procedure |
| `STATE_SOS_SOURCE` | 11 | `TIMESTAMP WITH LOCAL TIME ZONE`; a `NUMBER` with no precision |

### The one that matters most

**Oracle stores the empty string as NULL. PostgreSQL stores it as a zero-length string.**

`UCC_DEBTOR.MAILING_ADDRESS_2` was written with `''` for about 1,400 rows. Oracle collapsed those
to NULL. Move the data with a CSV round-trip that does not distinguish the two and they arrive in
PostgreSQL as empty strings. Row counts match. Checksums look plausible. No constraint fires.

And every `WHERE mailing_address_2 IS NULL` in the application quietly stops matching them. The
report that used to say 1,400 says 0. Nobody notices for a quarter.

Your validator has to catch this. **On your first run it probably will not** — and that is the
exercise, not a bug in the lab.

## What You Build

| File | What goes in it |
|---|---|
| `hooks.py` | Four guardrails: Oracle read-only, PostgreSQL target protection, HITL cutover gate, redacted audit log |
| `type_mapping.py` | The Oracle→PostgreSQL type table, as testable code |
| `validation.py` | Row counts, NULL counts, the empty-string check, spot-check diffing |
| `coordinator.py` | Five-phase orchestration |
| `.claude/agents/*.md` | The five subagent definitions |

Everything else — `config.py`, both MCP tool servers, `observability/`, `report.py`,
`session.py`, `oracle_constructs.py` — is complete. You build the agent logic, not the plumbing.

**Build in this order.** Guardrails first, so nothing you write later can touch the source
database by accident:

1. `hooks.py` → `pytest tests/test_hooks_readonly.py tests/test_hooks_pg_guard.py tests/test_cutover_hitl.py`
2. `type_mapping.py` → `pytest tests/test_type_mapping.py`
3. `.claude/agents/*.md`
4. `coordinator.py`
5. `validation.py` → `pytest tests/test_validator_catches_empty_string.py`

Run the tests against your own work rather than the reference:

```bash
TEST_TARGET=starter pytest tests/ -v
```

## Running It

```bash
cd starter

# Everything, phases 1-5. Stops at the cutover gate.
docker compose run --rm agent python coordinator.py --migrate-all

# One phase at a time while you are building
docker compose run --rm agent python coordinator.py --phase schema

# Resume after an interruption -- skips completed phases
docker compose run --rm agent python coordinator.py --migrate-all --resume
```

Watch for `[guard] DENY` lines. Each one is a guardrail working. Read the reason before assuming
it is a bug.

## The Guardrails

Three of them run **before** the tool executes and return `PermissionResultDeny`, so the
dangerous call never happens. A hook that logs the `DROP` afterwards is an excellent post-mortem
and a useless guardrail.

1. **Oracle is read-only.** Built as an allow-list, not a deny-list. A deny-list of dangerous
   verbs is a losing game — you will remember `DROP` and forget `TRUNCATE`, or `FLASHBACK`, or a
   PL/SQL block wrapping an `UPDATE`. And the database user has `SELECT` and nothing else, so
   even a bug in the hook cannot write to production.
2. **The target is fenced.** No drops, and nothing created outside `ucc_migrated` — because
   cutover is one atomic `ALTER SCHEMA ... RENAME`, and a single object in `public` breaks it.
3. **Cutover needs a human.** `pg_cutover` is denied unless a person passed `--approve-cutover`,
   which sets an environment variable the agent can read and cannot write. Note what this does
   *not* do: it does not ask the model whether cutover seems reasonable. Self-approval is not a
   gate.
4. **Audit log.** Every tool call, with credentials redacted, in `migration_audit.jsonl`.

## Verify Everything Works

```bash
# 1. Unit tests -- no database, no API key needed
TEST_TARGET=starter pytest tests/ -v
# Expect: all green. ~150 assertions across type mapping, guardrails,
#         construct detection, and reconciliation.

# 2. Guardrails actually block
docker compose run --rm agent python -c "
import asyncio, hooks
print(asyncio.run(hooks.can_use_tool(
    'mcp__oracle_src__oracle_sample_rows',
    {'sql': 'DROP TABLE meridian.ucc_filing'}, None)).message)"
# Expect: Source database is read-only: DROP rejected...

# 3. Full migration
docker compose run --rm agent python coordinator.py --migrate-all

# 4. The planted bug is reported
cat artifacts/validation_summary.json | python -m json.tool
# Expect a BLOCKER on ucc_debtor.mailing_address_2

# 5. Fix the data-migrator subagent, re-run phase 3, re-validate
docker compose run --rm agent python coordinator.py --phase data
docker compose run --rm agent python coordinator.py --phase validate
# Expect: blockers: 0, cutover_recommended: true

# 6. Cutover is still blocked without a human
docker compose run --rm agent python coordinator.py --phase cutover
# Expect: CUTOVER REQUIRES HUMAN APPROVAL

# 7. Evaluation harness
docker compose run --rm agent python evaluation/test_suite.py
# Expect: >= 18/20
```

Compare your output against `expected_output/`.

## Spec-Driven: Build It Again in One Command

`spec/agent-spec.md` describes this entire system — tools, subagents, hooks, tests, acceptance
criteria. Once your hand-built version works:

```bash
claude "Read spec/agent-spec.md and build the entire project into generated/"
diff -ru solution/ generated/
```

The differences are the interesting part. Where they disagree, decide which is right and why.

Then change *the spec* — add a `performance-advisor` subagent that reads Oracle execution plans
and proposes indexes — regenerate, and watch the whole project absorb it without you editing six
files by hand. That is the actual lesson of Tier 3.

## Troubleshooting

**`ORA-12541: TNS:no listener`** — Oracle is still initializing. `docker compose ps` must show
`healthy`. First boot takes 1–3 minutes; on emulated ARM, longer.

**`ORA-01017: invalid username/password`** — the seed scripts run on **first boot only**. If you
edited `legacy-oracle/*.sql` after the volume was created, they did not re-run:
`docker compose down -v && docker compose up -d oracle`.

**Oracle container exits immediately, no logs** — usually memory. Oracle Free needs ~2 GB.
Raise Docker Desktop's memory limit to 6 GB.

**`ModuleNotFoundError: No module named 'oracledb'`** — you are running on the host instead of in
the container. Either `pip install -r requirements.txt`, or use
`docker compose run --rm agent ...`.

**`psycopg.errors.InvalidSchemaName: schema "ucc_migrated" does not exist`** — phase 2 did not
complete. Run `--phase schema` first; the phases are ordered for a reason.

**Validator reports zero defects on the first run** — be suspicious of yourself before you are
pleased. Either `detect_empty_string_divergence` is not being called, or `pg_checksum` is not
being asked for `mailing_address_2`. An empty defect list and a validator that never ran look
identical in the JSON.

**Agent says "I'll work around the cutover gate"** — it should not, and if it does, your
`hitl_cutover_gate` is returning `PermissionResultAllow` on the wrong branch. Check
`tests/test_cutover_hitl.py`.

**Token budget exhausted mid-run** — `--resume` skips completed phases. Raise `TOKEN_BUDGET` in
`.env` if you genuinely need to, but first check `artifacts/migration_report.html` for which
object burned it; usually one subagent is looping.

## Going Further (all OPTIONAL)

1. Add a `performance-advisor` subagent that reads Oracle execution plans and proposes
   PostgreSQL indexes.
2. Emit a Flyway or Liquibase changeset instead of raw DDL.
3. Add change-data-capture for a zero-downtime cutover (logical replication).
4. Point the same spec at a MySQL target and diff what the agent produces.
5. Wire the migration report into the Grafana dashboards from M19/M20.

## What You Built

A migration system that reads a database it is not allowed to write to, generates code in a
language it was not given examples of, refuses the one conversion that has no safe answer, proves
its own output correct, and stops to ask a human before doing the one thing it cannot undo.

The refusal and the stop are the hard parts. Anyone can get an agent to produce DDL.
