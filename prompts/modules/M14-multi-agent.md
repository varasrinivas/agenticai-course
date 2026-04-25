# M14: Multi-Agent Systems

**Track**: 4 — Agent Architectures | **Position**: 14 of 30 | **Level**: Advanced
**Prerequisites**: M12, M13
**Estimated Time**: 75-90 minutes
**Track Color**: var(--track-architecture) / #F97316

## Concepts
- When one agent isn't enough — the "team of specialists" model
- Architecture patterns: supervisor/worker, peer-to-peer, pipeline (animated comparisons)
- Agent communication: explicit context passing vs shared state
- Why subagents DON'T inherit the coordinator's context (isolated context windows)
- Conflict resolution: what if agents disagree?
- Visual: Animated multi-agent collaboration with message flow

## Hands-On Lab
Build a content creation pipeline with 4 agents: researcher (searches filings), analyst (identifies patterns), writer (generates report), reviewer (checks accuracy). Coordinator delegates and aggregates.

## Quiz Focus (5 questions)
1. When should you use multi-agent vs single agent with many tools? (multi-agent when tools exceed 5-8 or specialization helps)
2. Do subagents see the coordinator's conversation? (no — isolated context, explicit handoff)
3. What's the supervisor/worker pattern? (one coordinator delegates to specialist workers)
4. More agents = better? (no — communication overhead, harder to debug)
5. How do you handle a subagent failure? (coordinator catches error, retries or routes to fallback)
