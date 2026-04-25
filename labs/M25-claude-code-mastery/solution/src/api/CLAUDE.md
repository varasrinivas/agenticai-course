# API Layer — Directory-Level Configuration

This CLAUDE.md applies ONLY to files within `src/api/` and its subdirectories.
It extends (does not replace) the project-level `.claude/CLAUDE.md`.

## Endpoint Standards
- All endpoints must return JSON responses (never plain text or HTML)
- Use proper HTTP status codes:
  - `400` — Bad request (malformed input, missing required fields)
  - `401` — Unauthorized (missing or invalid Bearer token)
  - `404` — Not found (filing, debtor, or resource does not exist)
  - `422` — Validation error (input parses but fails business rules, e.g., invalid state code)
  - `500` — Internal server error (always log full traceback via structlog)
- Every response must include a `request_id` field (UUID v4) for tracing
- Error responses follow the schema: `{"error": str, "request_id": str, "detail": str | null}`

## Rate Limiting
- All endpoints return rate limit headers:
  - `X-RateLimit-Limit` — max requests per window
  - `X-RateLimit-Remaining` — requests left in current window
  - `X-RateLimit-Reset` — Unix timestamp when the window resets
- Throttled requests return `429 Too Many Requests` with a `Retry-After` header
- Rate limit response body: `{"error": "rate_limited", "retry_after_seconds": int}`

## Authentication
- All endpoints require a Bearer token in the `Authorization` header
- Tokens are validated in the FastAPI middleware (`src/api/middleware/auth.py`)
- On invalid or expired token: return `401` with `{"error": "unauthorized", "detail": "Token expired or invalid"}`
- Exempt endpoints: `GET /health`, `GET /ready` (no auth required)
