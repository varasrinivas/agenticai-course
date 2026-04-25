#!/usr/bin/env bash
# Tier 2: GCP Cloud Run Deployment
# Bronze Layer Data Validation Pipeline
#
# Usage: ./deploy.sh
# Prereqs: gcloud CLI authenticated, project created
# Docs: See solution/deploy/gcp/deploy.sh for reference

set -euo pipefail

# TODO 1: Configure project, region, service name
#   PROJECT_ID="your-gcp-project-id"
#   REGION="us-central1"
#   SERVICE_NAME="bronze-validator"
#   REPO_NAME="bronze-validator-repo"

# TODO 2: Create Artifact Registry repo
#   gcloud artifacts repositories create $REPO_NAME \
#     --repository-format=docker \
#     --location=$REGION \
#     --description="Bronze validator container images"

# TODO 3: Build and push Docker image
#   IMAGE_URI="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${SERVICE_NAME}:latest"
#   gcloud builds submit --tag $IMAGE_URI .

# TODO 4: Deploy to Cloud Run with secrets
#   gcloud run deploy $SERVICE_NAME \
#     --image $IMAGE_URI \
#     --region $REGION \
#     --memory 1Gi \
#     --timeout 900 \
#     --set-secrets "ANTHROPIC_API_KEY=anthropic-api-key:latest" \
#     --no-allow-unauthenticated

# TODO 5: Print service URL
#   SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)')
#   echo "Deployed to: $SERVICE_URL"
