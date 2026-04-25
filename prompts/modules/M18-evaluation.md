# M18: Evaluation & Testing

**Track**: 5 — Guardrails & Safety | **Position**: 18 of 30 | **Level**: Intermediate → Advanced
**Prerequisites**: M12, M16, M17
**Estimated Time**: 60-75 minutes
**Track Color**: var(--track-guardrails) / #EF4444

## Concepts
- Why agent testing differs from software testing (non-deterministic, multiple valid answers)
- Evaluation metrics: task completion rate, tool accuracy, response quality, latency
- Claude-as-judge: using a second Claude call to evaluate the first
- A/B testing for agents: comparing prompts, tools, strategies
- Regression testing: ensuring changes don't break existing behavior
- Evaluation datasets: building and maintaining test suites

## Hands-On Lab
Build an eval harness that scores the UCC research agent on 50 test cases. Metrics: correct filing found (binary), entity resolution accuracy (fuzzy match score), response quality (Claude-as-judge). Generate an eval report with per-type breakdown.

## Quiz Focus (5 questions)
1. Why can't you just use unit tests for agents? (non-deterministic outputs, multiple valid paths)
2. What does Claude-as-judge mean? (use a separate Claude call to score the agent's response)
3. Aggregate metrics hide failures — explain? (95% overall accuracy could mask 40% failure on one category)
4. Do eval datasets need updating? (yes — as the domain changes, test cases become stale)
5. Passing tests = production-ready? (no — tests cover known cases, production has unknowns)
