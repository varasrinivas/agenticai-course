#!/bin/bash
# M22B: Test all three deployments with the same query
# ======================================================
# Usage:
#   export GCP_SERVICE_URL=https://your-cloud-run-url
#   export AWS_API_URL=https://your-api-gateway-url
#   ./test_all.sh

LOCAL_URL="http://localhost:8000"
GCP_URL="${GCP_SERVICE_URL:-http://localhost:8000}"
AWS_URL="${AWS_API_URL:-http://localhost:8000}"

QUERY='{"query": "Find all UCC filings for Acme Corporation in New York"}'

echo "============================================================"
echo "  M22B: Testing All Three Deployments"
echo "============================================================"
echo ""

# --- Local Docker ---
echo "1. LOCAL DOCKER ($LOCAL_URL)"
echo "------------------------------------------------------------"
echo "   Health check:"
curl -s $LOCAL_URL/health | python3 -m json.tool 2>/dev/null || echo "   FAILED — is the container running?"
echo ""
echo "   Query (with timing):"
time curl -s -X POST $LOCAL_URL/query \
    -H "Content-Type: application/json" \
    -d "$QUERY" | python3 -m json.tool 2>/dev/null || echo "   FAILED"
echo ""

# --- Google Cloud Run ---
echo "2. GOOGLE CLOUD RUN ($GCP_URL)"
echo "------------------------------------------------------------"
if [ "$GCP_URL" = "http://localhost:8000" ]; then
    echo "   SKIPPED — set GCP_SERVICE_URL to test Cloud Run"
else
    echo "   Health check:"
    curl -s $GCP_URL/health | python3 -m json.tool 2>/dev/null || echo "   FAILED"
    echo ""
    echo "   Query (with timing):"
    time curl -s -X POST $GCP_URL/query \
        -H "Content-Type: application/json" \
        -d "$QUERY" | python3 -m json.tool 2>/dev/null || echo "   FAILED"
fi
echo ""

# --- AWS Lambda ---
echo "3. AWS LAMBDA ($AWS_URL)"
echo "------------------------------------------------------------"
if [ "$AWS_URL" = "http://localhost:8000" ]; then
    echo "   SKIPPED — set AWS_API_URL to test Lambda"
else
    echo "   Health check:"
    curl -s $AWS_URL/health | python3 -m json.tool 2>/dev/null || echo "   FAILED"
    echo ""
    echo "   Query (with timing):"
    time curl -s -X POST $AWS_URL/query \
        -H "Content-Type: application/json" \
        -d "$QUERY" | python3 -m json.tool 2>/dev/null || echo "   FAILED"
fi
echo ""

# --- Comparison Table ---
echo "============================================================"
echo "  Deployment Comparison"
echo "============================================================"
echo ""
echo "| Environment   | Cold Start | Max Timeout | Cost at 0 Traffic  | Scaling       |"
echo "|---------------|-----------|-------------|-------------------|--------------|"
echo "| Local Docker  | None      | Unlimited   | \$0 (your machine) | Manual        |"
echo "| Cloud Run     | ~1-2s     | 60 min      | \$0 (scale to 0)   | Auto 0-1000   |"
echo "| AWS Lambda    | ~2-5s     | 15 min      | \$0 (scale to 0)   | Auto 0-1000   |"
echo ""
echo "============================================================"
echo "  All tests complete!"
echo "============================================================"
