# UCC Filing Pipeline — Claude Code Configuration

## Project Identity
<!-- TODO: Describe the project in 2-3 sentences -->
<!-- What does this system do? What domain does it serve? -->
<!-- Hint: UCC = Uniform Commercial Code. This system processes public filing records. -->

## Tech Stack
<!-- TODO: List the tech stack -->
<!-- Include: backend language/framework, database, queue, search engine, frontend, infrastructure -->

## Coding Standards
<!-- TODO: Define formatting and linting rules for Python and TypeScript -->
<!-- Python: which formatter? which linter? type hint requirements? -->
<!-- TypeScript: which linter? which formatter? strict mode? -->
<!-- TODO: Add logging rule (hint: never use print() — what should you use instead?) -->
<!-- TODO: Add test file naming convention (e.g., src/foo.py -> tests/test_foo.py) -->
<!-- TODO: Add OpenAPI docstring requirement for API endpoints -->

## Domain Rules
<!-- TODO: Define the filing number format (UCC-????-??-???????) -->
<!-- TODO: How are monetary values stored? (hint: integers representing what unit?) -->
<!-- TODO: How should debtor names be normalized before comparison? -->
<!-- TODO: What format are state codes? (length? case?) -->
<!-- TODO: What are the expiration rules for UCC-1 and UCC-3 filings? -->

## API Conventions
<!-- TODO: Which Claude API should always be used? (Messages API vs legacy?) -->
<!-- TODO: What must all tool definitions include for error handling? -->
<!-- TODO: How should structured output be extracted? (tool_use vs text parsing?) -->
<!-- TODO: What are the rate limits for batch vs real-time operations? -->

## Testing
<!-- TODO: Must every PR include tests? -->
<!-- TODO: Should integration tests use mocks or a real test database? -->
<!-- TODO: Which pytest plugin for async test functions? -->
<!-- TODO: What is the minimum coverage threshold for new code? -->
