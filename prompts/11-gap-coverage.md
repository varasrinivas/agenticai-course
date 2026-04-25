# Course Gap Analysis & Coverage Plan

These are topics that a production agent developer needs but the course currently covers lightly or not at all. Rather than adding new modules, these should be woven into EXISTING modules as additional sections.

The `/fix-explanations` command should add these sections during the fix phase.

---

## GAP 1: Error Handling & Retry Patterns
**Priority**: HIGH — every production agent needs this
**Add to**: M12 (ReAct) and M21 (API Design)

Add to M12 after the ReAct loop:
- What happens when a tool call fails? (API timeout, invalid response, rate limit)
- Retry strategies: immediate retry, exponential backoff, retry with modified input
- Fallback chains: if tool A fails, try tool B
- Graceful degradation: return partial results instead of failing entirely
- Circuit breaker recap (preview M17)

Pseudocode:
```
FOR each tool call:
  TRY up to 3 times:
    result = CALL tool with exponential backoff (1s, 2s, 4s)
    IF success: BREAK
  IF all retries failed:
    IF fallback tool exists: TRY fallback
    ELSE: return partial results with error note
```

Add to M21:
- HTTP retry logic (429, 500, 503)
- Idempotency: safe to retry without duplicate side effects
- Dead letter queues for failed requests

---

## GAP 2: Streaming Responses
**Priority**: HIGH — critical UX for agents (responses take 5-30 seconds)
**Add to**: M21 (API Design) — expand from mention to full section

- Server-Sent Events (SSE) vs WebSocket vs long polling
- Claude's streaming API: `stream=True`, delta events, content block types
- Implementing streaming in FastAPI:
  ```
  FUNCTION stream_response(question):
    FOR each chunk FROM claude.stream(question):
      YIELD chunk as SSE event
      IF chunk is tool_use:
        EXECUTE tool
        YIELD tool result as progress event
  ```
- Client-side: how to consume SSE in browser/mobile
- Progress indicators: "Searching filings..." → "Found 7 results..." → "Generating report..."
- Why streaming matters: a 15-second wait with no feedback = user thinks it's broken

---

## GAP 3: Authentication & Authorization
**Priority**: HIGH — can't deploy without this
**Add to**: M21 (API Design) — new section after deployment

- API key authentication (simplest — for internal tools)
- OAuth 2.0 / JWT for user-facing agents
- Role-based access: which users can trigger which agent actions
- Tool-level permissions: agent can read filings but not delete them
- Rate limiting per user, not just per API

Pseudocode:
```
MIDDLEWARE authenticate(request):
  token = EXTRACT from request header
  user = VERIFY token
  IF not valid: RETURN 401
  request.user = user
  request.permissions = LOOKUP user roles

MIDDLEWARE authorize_tool(tool_name, user):
  IF tool_name NOT IN user.allowed_tools:
    RETURN "Agent cannot use {tool_name} for your role"
```

---

## GAP 4: Prompt Caching
**Priority**: HIGH — 90% cost reduction on repeated system prompts
**Add to**: M22 (Cost Optimization) — dedicated section

- Anthropic's prompt caching: cache long system prompts across API calls
- How it works: first call = full price + cache write, subsequent calls = cache hit (90% cheaper)
- Cache TTL: 5 minutes (extend by using within window)
- What to cache: system prompts, few-shot examples, RAG context prefixes
- What NOT to cache: user messages, tool results (unique per call)
- Cost math: 1000 calls with 4K-token system prompt → $X without cache → $Y with cache

---

## GAP 5: Extended Thinking
**Priority**: MEDIUM — improves complex reasoning significantly
**Add to**: M12 (ReAct) or M13 (Planning)

- What is extended thinking? Claude shows its internal reasoning before responding
- When to use: complex multi-step problems, math, logic, code analysis
- API parameter: `thinking: {type: "enabled", budget_tokens: 5000}`
- Reading thinking blocks: separate from the response content
- Cost: thinking tokens are billed but at a lower rate
- When NOT to use: simple lookups, latency-sensitive applications

---

## GAP 6: Multi-Modal Agents (Vision + PDF)
**Priority**: MEDIUM — increasingly common use case
**Add to**: M04 (Structured Output) or new section in M09 (RAG)

- Sending images to Claude: base64 encoding, media types
- Vision use cases for agents: read a scanned UCC filing, extract data from a photo of a document, analyze a chart
- PDF processing: Anthropic's document understanding vs external OCR
- Multi-modal RAG: embedding images alongside text
- Tool that processes images:
  ```
  TOOL analyze_document(image_base64):
    SEND to Claude with vision
    EXTRACT: filing number, debtor name, dates
    RETURN structured data
  ```

---

## GAP 7: Batch API
**Priority**: MEDIUM — 50% cost savings for non-real-time work
**Add to**: M22 (Cost Optimization)

- What: send up to 10,000 requests, get results within 24 hours
- 50% discount vs real-time API
- Use cases: nightly evaluation runs, bulk document processing, batch entity resolution
- Implementation: create batch → poll for completion → download results
- Perfect for: CAPSTONE-6 (run all 50 state validations as a batch job overnight)

---

## GAP 8: Prompt Management & Versioning
**Priority**: MEDIUM — important for teams
**Add to**: M19 (Tracing) or M20 (Monitoring)

- The problem: system prompts are code — they need versioning, review, testing
- Prompt-as-code: store prompts in version control, not hardcoded strings
- A/B testing prompts: route 10% to new prompt, compare metrics
- Prompt regression testing: run eval suite when prompt changes
- Tools: Langfuse prompt management, custom prompt registry

---

## GAP 9: Compliance & Audit Logging
**Priority**: MEDIUM — required for healthcare (HIPAA), finance (SOC2), EU (GDPR)
**Add to**: M19 (Tracing) — new section

- What to log for compliance: who asked, what the agent did, what tools it called, what data it accessed, what it returned
- What NOT to log: PII, PHI, passwords, full API keys
- PII redaction in logs: detect and mask before writing
- Audit trail requirements: immutable, tamper-proof, time-stamped
- Data retention policies: how long to keep traces
- GDPR right-to-deletion: can you delete traces that contain user data?

---

## GAP 10: Agent Versioning & Rollback
**Priority**: LOW — important for mature production systems
**Add to**: M20 (Monitoring) or M21 (API Design)

- The problem: you update a system prompt and agent performance degrades
- Canary deployments: route 5% of traffic to new version, compare metrics
- Feature flags for agent behavior: enable/disable tools, change routing logic
- Rollback strategy: instant revert to previous prompt/tool configuration
- Version tagging: every deployment gets a version number tied to eval results

---

## Implementation Plan

The build script's FIX phase already runs `/fix-explanations` on every module. To incorporate these gaps, update the fix-explanations command to also check:

**For modules M12, M13**: Add error handling patterns, extended thinking section
**For module M21**: Add streaming deep-dive, authentication section, retry patterns
**For module M22**: Add prompt caching section, batch API section
**For module M19**: Add compliance logging, prompt versioning
**For module M20**: Add agent versioning, rollback strategy
**For module M04 or M09**: Add multi-modal (vision + PDF) section

This keeps the course at 30 modules but increases depth where it matters most. Estimated addition: ~200-300 words per module for the applicable gaps.
