# M22: Cost Optimization

**Track**: 7 — Production Deployment | **Position**: 22 of 30 | **Level**: Intermediate → Advanced
**Prerequisites**: M02, M12, M21
**Estimated Time**: 50-60 minutes
**Track Color**: var(--track-deployment) / #3B82F6

## Concepts
- Cost anatomy of an agent call (animated breakdown: LLM tokens + tools + retrieval + compute)
- Caching strategies: prompt caching, response caching, embedding caching
- Model routing: Haiku for simple tasks, Sonnet for moderate, Opus for complex
- Token optimization: system prompt compression, output constraints, fewer turns
- Batch API: 50% discount for non-time-sensitive workloads
- Interactive: Cost calculator showing before/after optimization

## Hands-On Lab
Add caching + model routing to the UCC agent. Route filing lookups to Haiku ($0.25/1M tokens), entity resolution to Sonnet ($3/1M), complex risk analysis to Opus ($15/1M). Add response caching for repeated queries. Measure cost reduction vs baseline.

## Quiz Focus (5 questions)
1. What is model routing? (using cheaper models for simple tasks, expensive for complex)
2. Caching can serve stale data — when is this a problem? (when underlying data changes frequently)
3. Cheaper model = same quality? (no — Haiku may miss nuance that Opus catches, test before routing)
4. What is prompt caching? (Anthropic caches long system prompts, reducing cost on repeat calls)
5. What is premature optimization? (optimizing cost before proving the agent works correctly)
