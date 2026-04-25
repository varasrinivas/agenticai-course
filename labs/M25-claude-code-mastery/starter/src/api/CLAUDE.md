# API Layer — Directory-Level Configuration

<!-- This CLAUDE.md applies ONLY to files within src/api/ and its subdirectories. -->
<!-- It extends (does not replace) the project-level .claude/CLAUDE.md. -->

## Endpoint Standards
<!-- TODO: What format must all endpoints return? -->
<!-- TODO: List the HTTP status codes that must be used and when -->
<!--   Hint: 400 = bad request, 401 = unauthorized, 404 = not found, 422 = validation error, 500 = server error -->
<!-- TODO: What must be included in every response? (hint: request ID) -->

## Rate Limiting
<!-- TODO: What rate limit headers should endpoints return? -->
<!--   Hint: X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset -->
<!-- TODO: What HTTP status code for throttled requests? -->
<!-- TODO: What should the response body include when rate limited? -->

## Authentication
<!-- TODO: What authentication pattern is used? (hint: Bearer token) -->
<!-- TODO: Where are tokens validated? (middleware? decorator? each endpoint?) -->
<!-- TODO: What happens on invalid/expired token? (status code? response body?) -->
<!-- TODO: Are there any endpoints exempt from auth? (e.g., health check) -->
