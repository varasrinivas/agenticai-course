# M21: API Design & Deployment

**Track**: 7 — Production Deployment | **Position**: 21 of 30 | **Level**: Intermediate → Advanced
**Prerequisites**: M12, M16-M17, M19
**Estimated Time**: 60-75 minutes
**Track Color**: var(--track-deployment) / #3B82F6

## Concepts
- Designing the agent API: REST vs WebSocket vs Server-Sent Events
- Why streaming matters for agents (responses take 5-30 seconds, user needs progress)
- Request/response design: async job queues vs synchronous endpoints
- Containerization: Docker packaging for agent applications
- Cloud deployment patterns: serverless vs container-based
- Scaling: handling concurrent agent requests (queue-based processing)

## Hands-On Lab
Deploy the UCC agent as a production FastAPI application with: POST /query (synchronous), POST /query/stream (SSE streaming), GET /health (health check). Package in Docker. Test both endpoints with curl.

## Quiz Focus (5 questions)
1. Why streaming for agents? (agent loops take seconds, user sees progress instead of waiting)
2. localhost = production? (no — need auth, TLS, error handling, scaling, monitoring)
3. When use async job queue vs synchronous? (async for long-running tasks >30s, sync for quick responses)
4. What does a health check endpoint do? (load balancers and orchestrators use it to verify the service is alive)
5. How do you handle concurrent agent requests? (queue-based processing, limit concurrent LLM calls to control cost)
