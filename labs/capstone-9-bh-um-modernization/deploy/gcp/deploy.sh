#!/usr/bin/env bash
# Deploy the modernization agent as a Cloud Run JOB (not a service).
#
# Six phases run for minutes to hours and then finish. That is a job. Behind an
# HTTP endpoint you fight a 60-minute request ceiling for no benefit.
#
# Prerequisites:
#   gcloud auth login && gcloud config set project YOUR_PROJECT
#   A GCS bucket for artifacts -- the gap register is the deliverable and it
#   must outlive the container.
#
# Run from the lab root:
#   ./deploy/gcp/deploy.sh
set -euo pipefail

PROJECT="${GCP_PROJECT:?set GCP_PROJECT}"
REGION="${GCP_REGION:-us-central1}"
BUCKET="${ARTIFACT_BUCKET:?set ARTIFACT_BUCKET}"
JOB="bh-um-modernization-agent"
IMAGE="${REGION}-docker.pkg.dev/${PROJECT}/modernization/${JOB}:$(git rev-parse --short HEAD)"

echo "==> Building ${IMAGE}"
gcloud builds submit ./solution --project "${PROJECT}" --tag "${IMAGE}"

echo "==> Deploying job ${JOB}"
gcloud run jobs deploy "${JOB}" \
  --project "${PROJECT}" \
  --region "${REGION}" \
  --image "${IMAGE}" \
  --task-timeout 3600s \
  --max-retries 0 \
  --memory 2Gi \
  --set-secrets "ANTHROPIC_API_KEY=anthropic-api-key:latest" \
  --set-env-vars "^;^ARTIFACT_DIR=/mnt/artifacts;AUDIT_LOG=/mnt/artifacts/modernization_audit.jsonl;BH_EMIT_ROOT=/mnt/artifacts/bh-um-lite;PHI_ALLOWLIST=/work/bhauthtrack/db/02_seed.sql" \
  --add-volume "name=artifacts,type=cloud-storage,bucket=${BUCKET}" \
  --add-volume-mount "volume=artifacts,mount-path=/mnt/artifacts"

# --max-retries 0 is deliberate. A retried run re-does completed phases and
# pays for them again; resume is explicit, via --resume against
# session_state.json in the bucket.

cat <<'NOTE'

==> Deployed. Two things before you run it:

  1. LOG RETENTION. The protected-content gate redacts before every write, but
     anything that reaches Cloud Logging has been copied into a system with its
     own retention and its own export sinks. Set retention deliberately on this
     project; a 400-day default is a 400-day retention on whatever the
     redaction missed.

  2. FINALIZATION IS A SEPARATE JOB. Do NOT add BH_FINALIZATION_APPROVED to the
     env vars above. The moment it lives in a manifest it is on by default,
     forever, for every future run, and the gate is gone. See approve-job.yaml.

Run it:
    gcloud run jobs execute bh-um-modernization-agent --region REGION --wait
NOTE
