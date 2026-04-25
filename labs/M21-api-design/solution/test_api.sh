#!/bin/bash
# M21: API Test Script
# Run this after starting the server with: python server.py

BASE_URL="http://localhost:8000"

echo "=== Testing UCC Agent API ==="
echo ""

echo "1. Health Check"
curl -s $BASE_URL/health | python -m json.tool
echo ""

echo "2. Sync Query"
curl -s -X POST $BASE_URL/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Find all UCC filings for Acme Corporation in New York"}' \
  | python -m json.tool
echo ""

echo "3. Streaming Query"
curl -s -N -X POST $BASE_URL/query/stream \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the risk level for Acme Corporation?"}'
echo ""
echo ""

echo "4. Error Handling (empty query)"
curl -s -X POST $BASE_URL/query \
  -H "Content-Type: application/json" \
  -d '{"query": ""}' \
  | python -m json.tool
echo ""

echo "=== All tests complete ==="
