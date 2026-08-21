#!/usr/bin/env bash
# Deploy the migration agent as a Cloud Run JOB (not a service).
#
# A migration runs for minutes to hours and then finishes. That is a job.
# Putting it behind an HTTP endpoint means fighting a 60-minute request
# ceiling for no benefit.
#
# Prerequisites:
#   gcloud auth login && gcloud config set project YOUR_PROJECT
#   A Cloud SQL for PostgreSQL instance
#   Network reachability to the source Oracle (VPN / Interconnect / proxy)
#
# Run from the repo root:
#   ./deploy/gcp/deploy.sh
set -euo pipefail

PROJECT="${GCP_PROJECT:?set GCP_PROJECT}"
REGION="${GCP_REGION:-us-central1}"
JOB="ucc-migration-agent"
IMAGE="${REGION}-docker.pkg.dev/${PROJECT}/migration/${JOB}:$(git rev-parse --short HEAD)"

echo "==> Building ${IMAGE}"
gcloud builds submit ./starter \
  --project "${PROJECT}" \
  --tag "${IMAGE}"

echo "==> Deploying migration job"
# Note what is NOT here: CUTOVER_APPROVED. It is deliberately absent, and
# it must stay absent. An approval flag that lives in a deploy script is
# not an approval -- it is a default that nobody remembers setting.
gcloud run jobs deploy "${JOB}" \
  --project "${PROJECT}" \
  --region "${REGION}" \
  --image "${IMAGE}" \
  --task-timeout 3600s \
  --max-retries 0 \
  --memory 2Gi \
  --cpu 2 \
  --set-cloudsql-instances "${PROJECT}:${REGION}:${PG_INSTANCE:?set PG_INSTANCE}" \
  --set-secrets "ANTHROPIC_API_KEY=anthropic-api-key:latest,\
ORACLE_PASSWORD=oracle-reader-password:latest,\
PG_PASSWORD=pg-migration-password:latest" \
  --set-env-vars "ORACLE_USER=migration_reader,\
ORACLE_DSN=${ORACLE_DSN:?set ORACLE_DSN},\
ORACLE_SCHEMA=MERIDIAN,\
PG_HOST=/cloudsql/${PROJECT}:${REGION}:${PG_INSTANCE},\
PG_DATABASE=meridian,\
PG_USER=migration,\
PG_TARGET_SCHEMA=ucc_migrated,\
ARTIFACT_DIR=/tmp/artifacts,\
ARTIFACT_BUCKET=gs://${PROJECT}-migration-artifacts" \
  --command python \
  --args coordinator.py,--migrate-all

echo "==> Deploying the CUTOVER job separately"
# Separate job, separate invocation, separate audit trail.
#
# The point is not technical -- it is that "run the migration" and
# "promote it to production" become two different things a person has to
# decide to do, minutes or days apart, with the validation report in
# between. Wiring cutover into the tail of the migration job would make
# the gate a formality.
gcloud run jobs deploy "${JOB}-cutover" \
  --project "${PROJECT}" \
  --region "${REGION}" \
  --image "${IMAGE}" \
  --task-timeout 600s \
  --max-retries 0 \
  --set-cloudsql-instances "${PROJECT}:${REGION}:${PG_INSTANCE}" \
  --set-secrets "ANTHROPIC_API_KEY=anthropic-api-key:latest,\
PG_PASSWORD=pg-migration-password:latest,\
CUTOVER_TOKEN=cutover-token:latest" \
  --set-env-vars "PG_HOST=/cloudsql/${PROJECT}:${REGION}:${PG_INSTANCE},\
PG_DATABASE=meridian,PG_USER=migration,PG_TARGET_SCHEMA=ucc_migrated" \
  --command python \
  --args coordinator.py,--phase,cutover,--approve-cutover

cat <<'NOTE'

Deployed.

  Run the migration:
      gcloud run jobs execute ucc-migration-agent --region REGION --wait

  Read the report BEFORE the next command:
      gsutil cp gs://PROJECT-migration-artifacts/migration_report.html .

  Then, only if a human has read it and agrees:
      gcloud run jobs execute ucc-migration-agent-cutover --region REGION --wait

Restrict run.jobs.run on the cutover job with IAM to whoever is allowed to
approve. The gate in hooks.py stops the AGENT from self-approving; IAM is
what stops everyone else.
NOTE
