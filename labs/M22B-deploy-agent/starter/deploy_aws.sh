#!/bin/bash
# M22B: Deploy to AWS Lambda
# ============================
# Prerequisites: AWS CLI, SAM CLI, Docker installed
#
# Usage:
#   export ANTHROPIC_API_KEY=your-key   # optional if using mock agent
#   export AWS_REGION=us-east-1         # optional, defaults to us-east-1
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

# TODO 1: Create S3 bucket for SAM artifacts (if not exists)
# SAM needs an S3 bucket to upload your code package before deploying.
# The "2>/dev/null || true" silently ignores the error if bucket exists.
# aws s3 mb s3://${S3_BUCKET} --region $REGION 2>/dev/null || true

# TODO 2: Build with SAM
# SAM builds your Lambda deployment package inside a Docker container
# that matches the Lambda runtime. This ensures native dependencies
# are compiled for the correct architecture (Amazon Linux 2).
# sam build --use-container

# TODO 3: Deploy with SAM
# Key flags:
#   --capabilities CAPABILITY_IAM: allows SAM to create IAM roles
#   --parameter-overrides: passes your API key to the CloudFormation template
#   --no-confirm-changeset: auto-approve (skip the manual confirmation)
# sam deploy \
#     --stack-name $STACK_NAME \
#     --s3-bucket $S3_BUCKET \
#     --region $REGION \
#     --capabilities CAPABILITY_IAM \
#     --parameter-overrides AnthropicApiKey="${ANTHROPIC_API_KEY:-mock}" \
#     --no-confirm-changeset

# TODO 4: Get the API Gateway URL
# SAM creates an API Gateway endpoint automatically. We read it from
# the CloudFormation stack outputs.
# API_URL=$(aws cloudformation describe-stacks \
#     --stack-name $STACK_NAME \
#     --region $REGION \
#     --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
#     --output text)
# echo ""
# echo "=== Deployment Complete ==="
# echo "API URL: $API_URL"

# TODO 5: Test the deployment
# echo ""
# echo "Testing health endpoint..."
# curl -s ${API_URL}/health | python3 -m json.tool
# echo ""
# echo "Testing query endpoint..."
# curl -s -X POST ${API_URL}/query \
#     -H "Content-Type: application/json" \
#     -d '{"query": "Find filings for Acme Corporation"}' \
#     | python3 -m json.tool
# echo ""
# echo "Done! Your agent is live at: $API_URL"
