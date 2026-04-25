# M22B: Deploy Your Agent — Local, GCP & AWS

**Track**: 7B — Applied Deployment | **Position**: After M22, before M23
**Prerequisites**: M15B (Build Complete Agent), M21 (API Design), M22 (Cost Optimization)
**Estimated Time**: 2-3 hours (hands-on deployment lab)
**Level**: Advanced
**Track Color**: var(--track-deployment) / #3B82F6

## Why This Module Must Exist
M21 teaches API design concepts and M22 teaches cost optimization, but neither has the student actually DEPLOY a running agent. This module takes the agent built in M15B and deploys it to three environments — local Docker, Google Cloud Run, and AWS Lambda. The student ends with a live URL they can call from anywhere.

## What the Student Deploys
The UCC Filing Research Agent from M15B, wrapped as:
- A **FastAPI** REST API with streaming support
- A **Docker** container that runs locally
- A **Google Cloud Run** service
- An **AWS Lambda** function (behind API Gateway)
- Each deployment gets tested with the same curl command

## Module Structure

### Section 1: Wrap the Agent as an API (30 min — lab)

**Step 1: Create the FastAPI wrapper**
- Complete `server.py` that exposes the coordinator agent as a REST API:
  - `POST /query` — send a question, get an answer (synchronous)
  - `POST /query/stream` — send a question, get streaming response (SSE)
  - `GET /health` — health check endpoint
- Request/response models with Pydantic
- CORS middleware for browser access
- Error handling: API key missing, Claude API down, tool failures

**Step 2: Test locally without Docker**
- Run: `uvicorn server:app --port 8000`
- Test: `curl -X POST http://localhost:8000/query -H "Content-Type: application/json" -d '{"question": "Find filings for Acme Corporation"}'`
- Expected output: JSON response with the agent's answer
- Test the streaming endpoint with curl
- Checkpoint: both endpoints return valid responses

**Step 3: Explain the API design decisions**
- Why FastAPI over Flask (async support, automatic docs, Pydantic validation)
- Why streaming matters for agents (responses take 5-30 seconds — user needs progress)
- Why a health check endpoint (load balancers, container orchestration need it)
- Animated: Request flow — Client → FastAPI → Coordinator Agent → Subagents → Tools → Response stream back

### Section 2: Deploy Locally with Docker (30 min — lab)

**Step 4: Create the Dockerfile**
- Multi-stage build (keep image small)
- Security: non-root user, no secrets in image
- Environment variables for ANTHROPIC_API_KEY (passed at runtime, never baked in)
- Complete Dockerfile with every line annotated (WHAT/WHY)

**Step 5: Build and run the container**
- Build: `docker build -t ucc-agent .`
- Run: `docker run -p 8000:8000 -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY ucc-agent`
- Test: same curl command as Step 2
- Checkpoint: identical response from Docker container as from local uvicorn
- Troubleshooting: 
  - "port already in use" → change to -p 8001:8000
  - "ANTHROPIC_API_KEY not set" → verify env var before docker run
  - Container exits immediately → check logs: `docker logs <container_id>`

**Step 6: Docker Compose for development**
- docker-compose.yml with environment variable file (.env)
- Hot reload for development (mount source code as volume)
- .env.example file (checked into git) vs .env (gitignored)
- Run: `docker compose up` → test → `docker compose down`

### Section 3: Deploy to Google Cloud Run (45 min — lab)

**Step 7: GCP prerequisites**
- What you need: GCP account (free tier works), gcloud CLI installed, a GCP project
- Setup commands:
  ```
  gcloud auth login
  gcloud config set project YOUR_PROJECT_ID
  gcloud services enable run.googleapis.com artifactregistry.googleapis.com
  ```
- Create Artifact Registry repo for Docker images
- Checkpoint: `gcloud config list` shows correct project

**Step 8: Push image to Artifact Registry**
- Tag: `docker tag ucc-agent us-docker.pkg.dev/YOUR_PROJECT/agents/ucc-agent:v1`
- Auth: `gcloud auth configure-docker us-docker.pkg.dev`
- Push: `docker push us-docker.pkg.dev/YOUR_PROJECT/agents/ucc-agent:v1`
- Checkpoint: image visible in GCP Console → Artifact Registry

**Step 9: Deploy to Cloud Run**
- Deploy command:
  ```
  gcloud run deploy ucc-agent \
    --image us-docker.pkg.dev/YOUR_PROJECT/agents/ucc-agent:v1 \
    --region us-central1 \
    --set-env-vars ANTHROPIC_API_KEY=your-key \
    --memory 512Mi \
    --cpu 1 \
    --timeout 60 \
    --max-instances 3 \
    --allow-unauthenticated
  ```
- Every flag explained (WHY 512Mi memory, WHY 60s timeout for agent loops, WHY max 3 instances for cost control)
- Expected output: URL like `https://ucc-agent-xxxxx.run.app`
- Test: `curl -X POST https://ucc-agent-xxxxx.run.app/query -H "Content-Type: application/json" -d '{"question": "Find filings for Acme Corporation"}'`
- Checkpoint: same response as local, from a public URL

**Step 10: Secure the deployment**
- Remove `--allow-unauthenticated` for production
- Add IAM authentication: `gcloud run services add-iam-policy-binding`
- Use Secret Manager for ANTHROPIC_API_KEY instead of env vars
- Cost callout: Cloud Run pricing (per-request, $0 when idle — ideal for agents)

### Section 4: Deploy to AWS Lambda (45 min — lab)

**Step 11: AWS prerequisites**
- What you need: AWS account (free tier works), AWS CLI installed, Docker
- Setup: `aws configure` with access key and region
- Why Lambda for agents: pay-per-invocation, scales to zero, 15-minute max timeout (enough for most agent loops)
- Tradeoff vs Cloud Run: Lambda has cold starts (2-5 seconds), Cloud Run has min instances option

**Step 12: Create Lambda-compatible handler**
- New file `lambda_handler.py` that wraps the same agent code
- Mangum adapter: converts API Gateway events to FastAPI/ASGI
- Or: native Lambda handler without FastAPI (simpler, fewer dependencies)
- Both approaches shown, explain when to use which

**Step 13: Package and deploy with AWS SAM**
- `template.yaml` (SAM template) with Lambda function + API Gateway
- Build: `sam build`
- Deploy: `sam deploy --guided`
- Every SAM template field explained
- Expected output: API Gateway URL like `https://xxxxx.execute-api.us-east-1.amazonaws.com/prod/query`
- Test: same curl command with AWS URL
- Checkpoint: response from AWS Lambda matches local response

**Step 14: Secure the AWS deployment**
- API Gateway API key for authentication
- Lambda environment variables for ANTHROPIC_API_KEY (encrypted at rest)
- IAM role with minimum permissions
- Cost callout: Lambda pricing (first 1M requests/month free, then $0.20/1M)

### Section 5: Deployment Comparison (15 min — concept)

**Animated comparison table:**

| | Local Docker | GCP Cloud Run | AWS Lambda |
|---|---|---|---|
| Cold start | None | ~1-2s (min instances: 0s) | ~2-5s |
| Max timeout | Unlimited | 60 min | 15 min |
| Cost at zero traffic | $0 | $0 | $0 |
| Scaling | Manual | Auto (0 to 1000) | Auto (0 to 1000) |
| Best for | Development, testing | Production APIs, predictable traffic | Event-driven, spiky traffic |
| Agent suitability | ✅ Full support | ✅ Best for most agents | ⚠️ Watch timeout for complex agents |

**When to use which:**
- Local Docker: always start here for development and testing
- Cloud Run: your default production choice (longest timeout, best DX, scales well)
- Lambda: event-driven agents (triggered by webhooks, S3 uploads, scheduled jobs)

### Section 6: Monitoring Your Deployed Agent (15 min — concept + quick lab)

**Step 15: Basic monitoring**
- GCP: Cloud Run logs in Cloud Console, request latency metrics
- AWS: CloudWatch logs, Lambda duration metrics
- Add a `/metrics` endpoint to your API that returns: total requests, average response time, error count
- "This is a preview — M19 and M20 cover full observability"

### Final Verification

**Step 16: Test all three deployments with the same query**
```bash
# Local
curl -s http://localhost:8000/query -H "Content-Type: application/json" \
  -d '{"question": "What is the lien exposure for Acme Corporation?"}' | jq .

# GCP Cloud Run
curl -s https://ucc-agent-xxxxx.run.app/query -H "Content-Type: application/json" \
  -d '{"question": "What is the lien exposure for Acme Corporation?"}' | jq .

# AWS Lambda
curl -s https://xxxxx.execute-api.us-east-1.amazonaws.com/prod/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the lien exposure for Acme Corporation?"}' | jq .
```
- All three should return equivalent responses
- 🎉 Congratulations: You have a multi-agent system running locally, on GCP, and on AWS

## Quiz Focus (5 questions)
1. Why use streaming for agent APIs? (responses take 5-30 seconds, user needs progress)
2. Why not bake ANTHROPIC_API_KEY into the Docker image? (security — images get committed/shared)
3. Cloud Run vs Lambda for an agent that takes 3 minutes to complete? (Cloud Run — Lambda max 15 min but Cloud Run is better for long-running)
4. What does --max-instances 3 prevent? (cost explosion from unexpected traffic)
5. Your agent works locally but returns timeout errors on Lambda. What's likely wrong? (agent loop takes longer than Lambda timeout — increase timeout or optimize)

## Rancher Desktop Alternative
For students whose organizations restrict Docker Desktop (paid license for enterprise), or who prefer a free open-source alternative: read `prompts/10-rancher-deployment.md` for complete Rancher Desktop instructions. Key points:
- If you choose dockerd runtime in Rancher: ALL commands in this module work as-is with zero changes
- If you choose containerd runtime: replace `docker` with `nerdctl` in every command
- Dockerfiles are IDENTICAL — no changes needed regardless of runtime
- Bonus: Rancher includes K3s (local Kubernetes) for optional K8s deployment exercise
