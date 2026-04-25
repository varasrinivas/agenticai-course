# UCC Filing Pipeline — Claude Code Configuration

## Project Identity
This is the UCC (Uniform Commercial Code) Filing Pipeline — a data engineering system that ingests, validates, enriches, and serves public UCC filing records across all 50 US states. It supports lien searches, debtor-creditor analysis, and filing lifecycle management for financial institutions and legal teams.

## Tech Stack
- Backend: Python 3.11 (FastAPI)
- Database: PostgreSQL 15 with pgvector
- Queue: Redis Streams
- Search: Elasticsearch 8
- Frontend: React 18 + TypeScript
- Infrastructure: Docker Compose (local), GCP Cloud Run (prod)

## Coding Standards
- Python: Format with black, lint with ruff, type hints on all public functions
- TypeScript: ESLint + Prettier, strict mode enabled
- All API endpoints must have OpenAPI docstrings
- Never use `print()` for logging — use `structlog`
- Test files mirror source: `src/api/filings.py` -> `tests/api/test_filings.py`

## Domain Rules
- Filing numbers follow format: UCC-YYYY-ST-NNNNNNN (e.g., UCC-2024-NY-0012847)
- All monetary values stored as integers (cents), displayed as dollars
- Debtor names must be normalized before comparison (uppercase, strip punctuation)
- State codes are always 2-letter uppercase abbreviations
- Expiration dates: UCC-1 = 5 years from filing, UCC-3 varies by amendment type

## API Conventions
- Always use Claude Messages API (never legacy completion API)
- All tool definitions must include error handling with isError field
- Structured output via tool_use, not text parsing
- Rate limit: Max 50 RPM for batch operations, 10 RPM for real-time

## Testing
- Every PR must include tests
- Integration tests use real test database (no mocks for data layer)
- Use `pytest-asyncio` for async test functions
- Minimum coverage: 80% for new code
