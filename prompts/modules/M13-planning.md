# M13: Planning & Task Decomposition

**Track**: 4 — Agent Architectures | **Position**: 13 of 30 | **Level**: Intermediate → Advanced
**Prerequisites**: M12
**Estimated Time**: 60-75 minutes
**Track Color**: var(--track-architecture) / #F97316
**SDK Tier**: 2 (dual-track). Lab ships `solution/` (manual planner that calls `client.messages.create()` for each plan step) AND `solution-sdk/` (planner expressed as a `query()` call with a `plan` tool, plus a worker subagent in `.claude/agents/executor.md`). See `prompts/19-sdk-tier-policy.md`.

## Concepts
- Why complex tasks need planning (the "IKEA furniture" analogy)
- Intent classification: understanding what the user actually wants
- Task decomposition: breaking big tasks into sub-tasks
- DAG execution: parallel vs sequential paths, dependency resolution
- Dynamic tool discovery: finding the right tools at runtime
- Visual: Animated DAG builder showing task dependencies and execution order

## Hands-On Lab
Build a planning agent that decomposes "Generate a complete risk report for Acme Corporation" into sub-tasks: search filings → resolve entity → calculate exposure → generate report. Execute as a DAG.

## Quiz Focus (5 questions)
1. When does a task need decomposition? (when it requires multiple tools in a specific order)
2. What is a DAG? (Directed Acyclic Graph — tasks with dependencies, no cycles)
3. Does every task need planning? (no — simple single-tool tasks don't benefit)
4. What's the risk of over-decomposition? (too many small tasks = overhead exceeds benefit)
5. How does the agent know the plan is complete? (all leaf nodes executed, results aggregated)
