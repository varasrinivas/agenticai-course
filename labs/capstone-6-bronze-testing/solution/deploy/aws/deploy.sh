#!/usr/bin/env bash
##############################################################################
# Tier 3: AWS Lambda Deployment
#
# Prerequisites:
#   - AWS SAM CLI installed
#   - AWS credentials configured (aws configure)
#   - ANTHROPIC_API_KEY stored in Secrets Manager as "anthropic-api-key"
#
# Usage:
#   cd deploy/aws
#   chmod +x deploy.sh
#   ./deploy.sh
##############################################################################

set -euo pipefail

# ── Configuration ───────────────────────────────────────────────────────────
STACK_NAME="${STACK_NAME:-bronze-validator}"
REGION="${AWS_REGION:-us-east-1}"
S3_BUCKET="${SAM_S3_BUCKET:?Set SAM_S3_BUCKET for SAM artifact storage}"

echo "============================================"
echo "Bronze Validator — AWS Lambda Deployment"
echo "============================================"
echo "Stack:  ${STACK_NAME}"
echo "Region: ${REGION}"
echo "Bucket: ${S3_BUCKET}"
echo ""

# ── Step 1: Validate the template ──────────────────────────────────────────
echo "==> Validating SAM template..."
sam validate --template-file template.yaml

# ── Step 2: Build ──────────────────────────────────────────────────────────
echo "==> Building SAM application..."
sam build \
    --template-file template.yaml \
    --use-container

# ── Step 3: Deploy ─────────────────────────────────────────────────────────
echo "==> Deploying to AWS Lambda..."
sam deploy \
    --stack-name "${STACK_NAME}" \
    --region "${REGION}" \
    --s3-bucket "${S3_BUCKET}" \
    --capabilities CAPABILITY_IAM \
    --no-confirm-changeset \
    --parameter-overrides \
        "AnthropicApiKeySecret=anthropic-api-key" \
        "MaxWorkers=5"

# ── Step 4: Print outputs ─────────────────────────────────────────────────
echo ""
echo "============================================"
echo "Deployment complete!"
echo "============================================"

aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}" \
    --region "${REGION}" \
    --query "Stacks[0].Outputs" \
    --output table

echo ""
echo "To invoke manually:"
echo "  aws lambda invoke --function-name ${STACK_NAME}-BronzeValidatorFunction \\"
echo "    --payload '{\"run_type\": \"full_seed\"}' \\"
echo "    --region ${REGION} \\"
echo "    output.json"
