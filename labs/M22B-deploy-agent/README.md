# M22B: Deploy Your Agent — Local Docker, GCP Cloud Run, AWS Lambda

## What You'll Build

You'll take the UCC Filing Research Agent from M15B and deploy it to three environments:

1. **Local Docker** — containerized on your machine
2. **Google Cloud Run** — serverless container on GCP
3. **AWS Lambda** — serverless function on AWS

By the end, you'll have a live URL you can call from anywhere with the same `curl` command.

## Prerequisites

- Completed M15B (Build Complete Agent)
- Completed M21 (API Design) and M22 (Cost Optimization)
- Docker Desktop installed and running
- Python 3.11+
- (Optional) GCP account with `gcloud` CLI installed
- (Optional) AWS account with AWS CLI + SAM CLI installed

## Time: 2-3 hours

## Quick Start

```bash
cd labs/M22B-deploy-agent/starter
cp .env.example .env
# Edit .env with your API key (or leave blank to use mock agent)
pip install -r requirements_api.txt
python server.py
# Visit http://localhost:8000/health
```

## Lab Steps

### Section 1: Wrap the Agent as an API (30 min)

The first step is turning your M15B agent into an HTTP API using FastAPI.

**Step 1: Review the models**

Open `starter/models.py` — this file is complete. It defines:
- `QueryRequest` — what the client sends (query string + optional parameters)
- `QueryResponse` — what the server returns (answer, filings, metadata)
- `HealthResponse` — for the `/health` endpoint
- `StreamChunk` — for Server-Sent Events streaming
- `ErrorResponse` — standardized error format

**Step 2: Review the mock agent**

Open `starter/mock_agent.py` — this file is complete. It provides a `MockUCCAgent` that returns realistic responses without needing an Anthropic API key. This lets you test the entire deployment pipeline locally.

**Step 3: Complete server.py**

Open `starter/server.py` and complete the 5 TODOs:
1. Create the FastAPI app with metadata (title, description, version)
2. Add CORS middleware so browsers can call your API
3. Implement the `GET /health` endpoint
4. Implement the `POST /query` endpoint (synchronous)
5. Implement the `POST /query/stream` endpoint (Server-Sent Events)

**Test locally:**
```bash
cd starter
uvicorn server:app --reload --port 8000

# In another terminal:
curl http://localhost:8000/health
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Find filings for Acme Corporation"}'
```

### Section 2: Deploy with Docker (30 min)

**Step 4: Complete the Dockerfile**

Open `starter/Dockerfile` and uncomment/complete the 7 TODOs:
1. Base image (python:3.11-slim)
2. Working directory
3. Install dependencies (copy requirements first for Docker layer caching)
4. Copy application code
5. Create non-root user (security best practice)
6. Expose port and add HEALTHCHECK
7. Start command with uvicorn

**Step 5: Complete docker-compose.yml**

Open `starter/docker-compose.yml` and complete the 7 TODOs:
1. Build context
2. Port mapping
3. Environment file
4. Environment variables
5. Health check
6. Restart policy
7. Volume mount for development

**Step 6: Build and run**

```bash
docker compose up --build

# Or in detached mode:
docker compose up --build -d
docker compose logs -f
```

**Step 7: Test with curl**

```bash
# Health check
curl http://localhost:8000/health

# Query
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Find all UCC filings for Acme Corporation in New York"}'

# Streaming
curl -N -X POST http://localhost:8000/query/stream \
  -H "Content-Type: application/json" \
  -d '{"query": "Find filings for Acme Corporation"}'
```

### Section 3: Deploy to Google Cloud Run (45 min)

> **Note:** This section requires a GCP account. Skip if you don't have one.

**Step 8: Set up your GCP project**

```bash
# Authenticate
gcloud auth login

# Set project
gcloud config set project YOUR_PROJECT_ID
export GCP_PROJECT_ID=YOUR_PROJECT_ID
```

**Step 9: Complete deploy_gcp.sh**

Open `starter/deploy_gcp.sh` and uncomment all TODOs. The script:
1. Enables required APIs (Cloud Run, Artifact Registry)
2. Creates an Artifact Registry repository
3. Configures Docker authentication
4. Builds and tags the Docker image
5. Pushes the image to Artifact Registry
6. Deploys to Cloud Run with resource limits
7. Retrieves the service URL
8. Tests the deployment

**Step 10: Deploy**

```bash
chmod +x deploy_gcp.sh
./deploy_gcp.sh
```

**Step 11: Test the deployed service**

```bash
# The deploy script prints the URL. Use it:
curl https://YOUR-SERVICE-URL/health
curl -X POST https://YOUR-SERVICE-URL/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Find filings for Acme Corporation"}'
```

### Section 4: Deploy to AWS Lambda (45 min)

> **Note:** This section requires an AWS account with SAM CLI. Skip if you don't have one.

**Step 12: Complete lambda_handler.py**

Open `starter/lambda_handler.py` and complete the 3 TODOs. This is the simplest file — Mangum adapts your FastAPI app to Lambda's event format in just 3 lines.

**Step 13: Complete template.yaml**

Open `starter/template.yaml` and uncomment the Lambda function resource. Key settings:
- Runtime: python3.11
- Handler: lambda_handler.handler
- Timeout: 300 seconds (agent queries can be slow)
- Memory: 512 MB
- API key passed as parameter with NoEcho

**Step 14: Deploy with SAM**

```bash
chmod +x deploy_aws.sh
./deploy_aws.sh
```

**Step 15: Test the deployed function**

```bash
# The deploy script prints the URL. Use it:
curl https://YOUR-API-GATEWAY-URL/health
curl -X POST https://YOUR-API-GATEWAY-URL/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Find filings for Acme Corporation"}'
```

### Section 5: Compare All Three (15 min)

**Step 16: Run the comparison test**

```bash
# Set your URLs
export GCP_SERVICE_URL=https://your-cloud-run-url
export AWS_API_URL=https://your-api-gateway-url

chmod +x test_all.sh
./test_all.sh
```

## Final Verification

The same curl command works against all three deployments:

```bash
curl -X POST $URL/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Find filings for Acme Corporation"}'
```

## Deployment Comparison

| Feature          | Local Docker     | GCP Cloud Run       | AWS Lambda          |
|-----------------|-----------------|--------------------|--------------------|
| Cold Start       | None            | ~1-2s              | ~2-5s              |
| Max Timeout      | Unlimited       | 60 min             | 15 min             |
| Cost at 0 Traffic| $0 (your machine)| $0 (scale to 0)   | $0 (scale to 0)   |
| Auto-scaling     | Manual          | 0-1000 instances   | 0-1000 concurrent  |
| HTTPS            | No (needs proxy)| Built-in           | Built-in           |
| Custom Domain    | Manual          | Cloud Run mapping  | API Gateway        |
| Streaming (SSE)  | Full support    | Full support       | Not supported*     |

*AWS Lambda with API Gateway does not natively support SSE. Use Lambda Function URLs or WebSocket API for streaming.

## Troubleshooting

**Docker build fails:**
- Make sure Docker Desktop is running
- Check that `requirements_api.txt` has no typos

**Port already in use:**
- `docker compose down` to stop existing containers
- Or change the port mapping in `docker-compose.yml`

**GCP deployment fails:**
- Check `gcloud auth list` to verify authentication
- Ensure billing is enabled on the project
- Check `gcloud run services list` for existing services

**AWS deployment fails:**
- Run `aws sts get-caller-identity` to verify credentials
- Ensure SAM CLI is installed: `sam --version`
- Check CloudFormation events: `aws cloudformation describe-stack-events --stack-name ucc-agent`

## Cleanup

```bash
# Local Docker
docker compose down

# GCP Cloud Run
gcloud run services delete ucc-agent --region us-central1

# AWS Lambda
sam delete --stack-name ucc-agent --region us-east-1
```

## File Structure

```
M22B-deploy-agent/
├── README.md                          # This file
├── starter/                           # Files with TODOs for you to complete
│   ├── models.py                      # Complete — Pydantic models
│   ├── mock_agent.py                  # Complete — Mock agent for testing
│   ├── server.py                      # TODO — FastAPI server
│   ├── Dockerfile                     # TODO — Docker image
│   ├── docker-compose.yml             # TODO — Local orchestration
│   ├── deploy_gcp.sh                  # TODO — GCP Cloud Run script
│   ├── deploy_aws.sh                  # TODO — AWS Lambda script
│   ├── lambda_handler.py              # TODO — Lambda adapter
│   ├── template.yaml                  # TODO — SAM template
│   ├── requirements_api.txt           # Complete — Python dependencies
│   ├── .env.example                   # Environment variable template
│   └── test_all.sh                    # Complete — Test all deployments
├── solution/                          # Complete solutions (Python + Node.js)
│   ├── server.py                      # Complete FastAPI server
│   ├── server.js                      # Complete Express server (Node.js)
│   ├── models.py                      # Pydantic models
│   ├── mock_agent.py                  # Mock agent
│   ├── Dockerfile                     # Production Dockerfile (Python)
│   ├── Dockerfile.node                # Production Dockerfile (Node.js)
│   ├── docker-compose.yml             # Complete compose file
│   ├── deploy_gcp.sh                  # Complete GCP script
│   ├── deploy_aws.sh                  # Complete AWS script
│   ├── lambda_handler.py              # Complete Lambda handler (Python)
│   ├── lambda_handler.js              # Complete Lambda handler (Node.js)
│   ├── template.yaml                  # Complete SAM template
│   ├── requirements_api.txt           # Python dependencies
│   ├── package.json                   # Node.js dependencies
│   ├── .env.example                   # Environment template
│   └── test_all.sh                    # Test script
└── expected_output/
    ├── local_test_output.txt          # Expected output from local Docker
    └── deployment_comparison.txt      # Side-by-side comparison
```
