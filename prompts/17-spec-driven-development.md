# Spec-Driven Agent Development

## The Pattern
1. Write agent-spec.md (12-section template)
2. claude "Read agent-spec.md and build everything"
3. Review generated code vs spec
4. Update spec -> targeted regeneration

## 12-Section Spec Template
1. Business Context
2. Agent Configuration (model, system prompt, limits)
3. Tools (name, params, returns, mock data, edge cases)
4. Hooks (PreToolUse, PostToolUse — logging, validation, redaction)
5. Guardrails (input/output validation, cost limits, circuit breaker)
6. Memory & Sessions (persistence, timeout, fork support)
7. API Design (endpoints, auth, rate limits, streaming)
8. Deployment (Docker + DuckDB local, GCP, AWS)
9. Observability (traces, audit log, PII exclusions)
10. Tests (unit, integration, edge cases)
11. Evaluation Dataset (10+ scenarios with expected behaviors)
12. File Structure (complete directory tree)

## Why Spec-Driven
- Individuals: write WHAT not HOW, iterate at design level
- Teams: architects write specs, code reviews become spec reviews
- Production: spec is living documentation, transfers across frameworks

Meta connection: this course was built spec-driven. Prompt files ARE the spec.
