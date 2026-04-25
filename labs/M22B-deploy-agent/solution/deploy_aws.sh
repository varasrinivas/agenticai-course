#!/bin/bash
# M22B: Deploy to AWS Lambda (Solution)
# ========================================
# Prerequisites: AWS CLI, SAM CLI, Docker installed
#
# Usage:
#   export ANTHROPIC_API_KEY=your-key
#   export AWS_REGION=us-east-1
#   ./deploy_aws.sh

set -e

STACK_NAME="ucc-agent"
REGION="${AWS_REGION:-us-east-1}"
S3_BUCKET="${SAM_S3_BUCKET:-ucc-agent-deploy-${RANDOM}}"

echo "=== Deploying UCC Agent to AWS Lambda ==="
echo "Stack:  $STACK_NAME"
echo "Region: $REGION"
echo "Bucket: $S3_BUCKET"
echo ""

# Step 1: Create S3 bucket for SAM artifacts (if not exists)
echo ">>> Creating S3 bucket for deployment artifacts..."
aws s3 mb s3://${S3_BUCKET} --region $REGION 2>/dev/null || true

# Step 2: Build with SAM
echo ">>> Building with SAM..."
sam build --use-container

# Step 3: Deploy with SAM
echo ">>> Deploying with SAM..."
sam deploy \
    --stack-name $STACK_NAME \
    --s3-bucket $S3_BUCKET \
    --region $REGION \
    --capabilities CAPABILITY_IAM \
    --parameter-overrides AnthropicApiKey="${ANTHROPIC_API_KEY:-mock}" \
    --no-confirm-changeset

# Step 4: Get the API Gateway URL
API_URL=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
    --output text)
echo ""
echo "=== Deployment Complete ==="
echo "API URL: $API_URL"

# Step 5: Test the deployment
echo ""
echo "Testing health endpoint..."
curl -s ${API_URL}/health | python3 -m json.tool
echo ""
echo "Testing query endpoint..."
curl -s -X POST ${API_URL}/query \
    -H "Content-Type: application/json" \
    -d '{"query": "Find filings for Acme Corporation"}' \
    | python3 -m json.tool
echo ""
echo "Done! Your agent is live at: $API_URL"
