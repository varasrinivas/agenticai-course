# M14: Multi-Agent Systems

**Track**: 4 — Agent Architectures | **Position**: 14 of 30 | **Level**: Advanced
**Prerequisites**: M12, M13
**Estimated Time**: 75-90 minutes
**Track Color**: var(--track-architecture) / #F97316
**SDK Tier**: 2 (dual-track). See `prompts/19-sdk-tier-policy.md`. Lab ships BOTH `solution/` (manual coordinator + worker pattern in Python) AND `solution-sdk/` (subagents declared as `.claude/agents/researcher.md`, `analyst.md`, `writer.md`, `reviewer.md` with `claude-agent-sdk` orchestration). The HTML must include a "Manual orchestration vs declarative subagents" side-by-side comparison.

## Concepts
- When one agent isn't enough — the "team of specialists" model
- Architecture patterns: supervisor/worker, peer-to-peer, pipeline (animated comparisons)
- Agent communication: explicit context passing vs shared state
- Why subagents DON'T inherit the coordinator's context (isolated context windows)
- Conflict resolution: what if agents disagree?
- Visual: Animated multi-agent collaboration with message flow

## Hands-On Lab
Build a content creation pipeline with 4 agents: researcher (searches filings), analyst (identifies patterns), writer (generates report), reviewer (checks accuracy). Coordinator delegates and aggregates.

**Two implementations**:
1. `solution/` — manual coordinator that calls each worker in a Python loop, passing explicit context dicts. Shows what's happening end-to-end.
2. `solution-sdk/` — each worker is a `.claude/agents/<name>.md` file with frontmatter (`name`, `description`, `tools`, `model`). The "coordinator" is a top-level `query()` call; subagent invocation happens declaratively. The student sees that the SDK turns ~150 lines of orchestration into ~30 lines + four markdown files.

## Quiz Focus (5 questions)
1. When should you use multi-agent vs single agent with many tools? (multi-agent when tools exceed 5-8 or specialization helps)
2. Do subagents see the coordinator's conversation? (no — isolated context, explicit handoff)
3. What's the supervisor/worker pattern? (one coordinator delegates to specialist workers)
4. More agents = better? (no — communication overhead, harder to debug)
5. How do you handle a subagent failure? (coordinator catches error, retries or routes to fallback)
