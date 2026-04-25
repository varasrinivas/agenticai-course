#!/bin/bash
# M22B: Deploy to Google Cloud Run (Solution)
# ==============================================
# Prerequisites: gcloud CLI installed, authenticated, project set
#
# Usage:
#   export GCP_PROJECT_ID=your-project-id
#   export ANTHROPIC_API_KEY=your-key
#   ./deploy_gcp.sh

set -e

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-your-project-id}"
REGION="us-central1"
SERVICE_NAME="ucc-agent"
IMAGE_NAME="ucc-agent-api"

echo "=== Deploying UCC Agent to Google Cloud Run ==="
echo "Project: $PROJECT_ID"
echo "Region:  $REGION"
echo ""

if [ "$PROJECT_ID" = "your-project-id" ]; then
    echo "ERROR: Set GCP_PROJECT_ID environment variable first."
    echo "  export GCP_PROJECT_ID=your-actual-project-id"
    exit 1
fi

# Step 1: Enable required APIs
echo ">>> Enabling required APIs..."
gcloud services enable run.googleapis.com artifactregistry.googleapis.com

# Step 2: Create Artifact Registry repository (if not exists)
echo ">>> Creating Artifact Registry repository..."
gcloud artifacts repositories create $SERVICE_NAME \
    --repository-format=docker \
    --location=$REGION \
    --description="UCC Agent Docker images" \
    2>/dev/null || echo "    Repository already exists"

# Step 3: Configure Docker authentication for Artifact Registry
echo ">>> Configuring Docker authentication..."
gcloud auth configure-docker ${REGION}-docker.pkg.dev --quiet

# Step 4: Build and tag the Docker image
echo ">>> Building Docker image..."
docker build -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/${SERVICE_NAME}/${IMAGE_NAME}:latest .

# Step 5: Push image to Artifact Registry
echo ">>> Pushing image to Artifact Registry..."
docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/${SERVICE_NAME}/${IMAGE_NAME}:latest

# Step 6: Deploy to Cloud Run
echo ">>> Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image ${REGION}-docker.pkg.dev/${PROJECT_ID}/${SERVICE_NAME}/${IMAGE_NAME}:latest \
    --region $REGION \
    --platform managed \
    --memory 1Gi \
    --cpu 1 \
    --timeout 300 \
    --max-instances 3 \
    --set-env-vars "ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-mock},ENVIRONMENT=gcp-cloud-run" \
    --allow-unauthenticated

# Step 7: Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
    --region $REGION \
    --format 'value(status.url)')
echo ""
echo "=== Deployment Complete ==="
echo "Service URL: $SERVICE_URL"

# Step 8: Test the deployment
echo ""
echo "Testing health endpoint..."
curl -s ${SERVICE_URL}/health | python3 -m json.tool
echo ""
echo "Testing query endpoint..."
curl -s -X POST ${SERVICE_URL}/query \
    -H "Content-Type: application/json" \
    -d '{"query": "Find filings for Acme Corporation"}' \
    | python3 -m json.tool
echo ""
echo "Done! Your agent is live at: $SERVICE_URL"
