# Deployment

Three tiers. **Tier 1 is the lab** — the other two exist so you can see what changes when a
migration stops being a laptop exercise, and they need a cloud account.

| Tier | Where | Source | Target | When you would use it |
|---|---|---|---|---|
| 1 | Local Docker Compose | `gvenzl/oracle-free` container | `postgres:16` container | The lab. Also a genuine dry-run pattern: restore a production Oracle backup into a throwaway container and rehearse the whole migration against it. |
| 2 | GCP Cloud Run job | On-prem Oracle via Cloud SQL Auth Proxy / VPN | Cloud SQL for PostgreSQL | Real migration where the source stays where it is |
| 3 | AWS ECS task | RDS for Oracle or on-prem | Aurora PostgreSQL | Same, in AWS |

## Why a job, not a service

Phases 1–5 run for minutes to hours and then finish. That is a **job**, not a request handler.
Deploying it behind an HTTP endpoint means fighting request timeouts for no benefit — Cloud Run
services cap at 60 minutes, Lambda at 15, and a real migration of a real database will exceed
both. Cloud Run *jobs* and ECS *tasks* have no such ceiling.

The cutover gate is the reason this matters more than it usually would. A job that dies at minute
59 leaves you resuming from `session_state.json`, which is fine. A job that dies *during* an
`ALTER SCHEMA RENAME` does not, which is why cutover is a separate, human-triggered invocation
rather than the last step of a long run.

## What changes between tiers

Almost nothing in the agent. `config.py` reads connection details from the environment, so the
only real differences are:

1. **Credentials.** Compose reads `.env`; Cloud Run reads Secret Manager; ECS reads Secrets
   Manager. Never bake them into the image — and note that `hooks.redact()` exists precisely
   because a DSN otherwise ends up in `migration_audit.jsonl`.
2. **Network path to the source.** The whole reason Tier 2 and 3 are harder: production Oracle is
   usually not reachable from a managed runtime without a VPN, Direct Connect, or a proxy.
3. **Artifact storage.** Locally, `artifacts/` is a bind mount. In the cloud it has to go to GCS
   or S3, or the generated DDL and diffs die with the container.
4. **The approval gate.** Locally it is a CLI flag. In the cloud it should be a separate,
   explicitly-invoked job — see `gcp/cutover-job.yaml`. Do not wire cutover into the same
   execution as the migration, and do not make the approval an environment variable someone can
   set in a config file and forget about.

## Files

- `local/` — points at the compose file in `starter/`; nothing extra needed
- `gcp/` — `cloudbuild.yaml`, `deploy.sh`, `cutover-job.yaml`
- `aws/` — `task-definition.json`, `deploy.sh`

Read `gcp/deploy.sh` even if you are on AWS. The comments explain the approval-gate split, which
is the part that is easy to get wrong in both clouds.
