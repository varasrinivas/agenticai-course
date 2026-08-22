# Deployment

Three tiers. **Tier 1 is the lab** — the other two exist so you can see what changes when a
modernization stops being a laptop exercise, and they need a cloud account.

| Tier | Where | Reads | Writes | When you would use it |
|---|---|---|---|---|
| 1 | Local Docker Compose | the two vendored source trees | `bh-um-lite/` on a bind mount | The lab |
| 2 | GCP Cloud Run job | a read-only clone of the monolith repo | GCS bucket | A real modernization where the source stays where it is |
| 3 | AWS ECS task | same, from CodeCommit or S3 | S3 | Same, in AWS |

## Why a job, not a service

Six phases run for minutes to hours and then finish. That is a **job**, not a request handler.
Behind an HTTP endpoint you fight request timeouts for no benefit — Cloud Run *services* cap at 60
minutes, Lambda at 15 — and a real run over a 1,800-line service class and seven templates will
exceed both. Cloud Run *jobs* and ECS *tasks* have no such ceiling.

## The thing that is different about this deployment

Most agent deployments worry about credentials and network reachability. Those matter here too.
But the constraint that shapes every tier is **"no PHI in prompts, ever"**, and it gets *harder*
in the cloud, not easier:

| | Local | Cloud |
|---|---|---|
| Where a blocked narrative could end up | one container's stdout | Cloud Logging, and whatever is subscribed to it |
| Who can read the audit log | you | anyone with project log-viewer |
| What a crash dump contains | a terminal | a retained log entry with a retention policy someone else set |

So the deployment rules are not optional decoration:

1. **`modernization_audit.jsonl` goes to object storage, not to stdout.** The redaction in
   `hooks.redact()` runs before every write, but a log line that reaches Cloud Logging has been
   copied into a system with its own retention, its own access control, and its own export sinks.
   Keep it in one place you control.
2. **Never mount the real BHAuthTrack production database.** The agent reads a repository, not a
   system. If your organisation's modernization needs real row counts, run the counting query
   yourself and hand the agent the number.
3. **`PHI_ALLOWLIST` must name only synthetic fixtures.** Widening it to a directory of real
   extracts defeats the entire control, and it is one environment variable away.
4. **Set log retention deliberately.** A 400-day default on a project that runs this agent is a
   400-day retention on whatever the redaction missed.

## What changes between tiers

Almost nothing in the agent — `config.py` reads every path from the environment. The real
differences:

1. **Credentials.** Compose reads `.env`; Cloud Run reads Secret Manager; ECS reads Secrets
   Manager. Never bake them into the image.
2. **Artifact storage.** Locally `artifacts/` and `bh-um-lite/` are bind mounts. In the cloud they
   must go to GCS or S3, or the gap register dies with the container — and the gap register is the
   deliverable.
3. **The approval gate.** Locally it is `--approve` on the CLI. In the cloud it must be a
   **separate, explicitly-invoked execution** — see `gcp/approve-job.yaml`.

   Do not wire finalization into the same execution as the run, and **do not make
   `BH_FINALIZATION_APPROVED` a value in a deployment manifest**. The moment it lives in a YAML
   file it is on by default, forever, for every future run, and the gate is gone. It belongs in
   the command line of a job someone types.

## Running tier 1

```bash
cd labs/capstone-9-bh-um-modernization
cp solution/.env.example solution/.env      # add your ANTHROPIC_API_KEY
docker compose up --build
```

The run stops at the finalization gate and prints the briefing. That is the expected end. To
approve, read `artifacts/modernization_report.html` and then:

```bash
docker compose run --rm agent python coordinator.py --phase finalize --approve
```

## What "done" looks like

Not a green build. `artifacts/parity-report.json` with nine checks, each reporting what it
scanned, and `artifacts/manual-review-queue.json` with entries in it. **A run that queues nothing
has guessed at something.**
