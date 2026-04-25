#!/usr/bin/env bash
##############################################################################
# Tier 2: GCP Cloud Run Deployment
#
# Prerequisites:
#   - gcloud CLI installed and authenticated
#   - A GCP project with Cloud Run and Artifact Registry enabled
#   - ANTHROPIC_API_KEY set as a Secret Manager secret
#
# Usage:
#   cd deploy/gcp
#   chmod +x deploy.sh
#   ./deploy.sh
##############################################################################

set -euo pipefail

# ── Configuration ───────────────────────────────────────────────────────────
PROJECT_ID="${GCP_PROJECT_ID:?Set GCP_PROJECT_ID environment variable}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="bronze-validator"
REPO_NAME="bronze-validator-repo"
IMAGE_TAG="us-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${SERVICE_NAME}:latest"
MEMORY="1Gi"
CPU="1"
TIMEOUT="300"
MAX_INSTANCES="1"

# ── Step 1: Create Artifact Registry repo (if needed) ──────────────────────
echo "==> Ensuring Artifact Registry repo exists..."
gcloud artifacts repositories describe "${REPO_NAME}" \
    --location="${REGION}" \
    --project="${PROJECT_ID}" 2>/dev/null \
|| gcloud artifacts repositories create "${REPO_NAME}" \
    --repository-format=docker \
    --location="${REGION}" \
    --project="${PROJECT_ID}" \
    --description="Bronze Validator images"

# ── Step 2: Build and push the image ───────────────────────────────────────
echo "==> Building and pushing Docker image..."
cd "$(dirname "$0")/../../"  # Navigate to solution root
gcloud builds submit \
    --project="${PROJECT_ID}" \
    --tag="${IMAGE_TAG}" \
    .

# ── Step 3: Deploy to Cloud Run ───────────────────────────────────────────
echo "==> Deploying to Cloud Run..."
gcloud run deploy "${SERVICE_NAME}" \
    --project="${PROJECT_ID}" \
    --region="${REGION}" \
    --image="${IMAGE_TAG}" \
    --memory="${MEMORY}" \
    --cpu="${CPU}" \
    --timeout="${TIMEOUT}" \
    --max-instances="${MAX_INSTANCES}" \
    --set-secrets="ANTHROPIC_API_KEY=anthropic-api-key:latest" \
    --no-allow-unauthenticated \
    --platform=managed

# ── Step 4: Print service URL ──────────────────────────────────────────────
SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" \
    --project="${PROJECT_ID}" \
    --region="${REGION}" \
    --format="value(status.url)")

echo ""
echo "============================================"
echo "Deployment complete!"
echo "Service URL: ${SERVICE_URL}"
echo "============================================"
echo ""
echo "To invoke:"
echo "  curl -H \"Authorization: Bearer \$(gcloud auth print-identity-token)\" ${SERVICE_URL}"
