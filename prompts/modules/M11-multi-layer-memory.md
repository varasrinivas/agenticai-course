# M11: Multi-Layer Memory Architecture

**Track**: 3 — Memory & Context | **Position**: 11 of 30 | **Level**: Advanced
**Prerequisites**: M08, M09
**Estimated Time**: 60-75 minutes
**Track Color**: var(--track-memory) / #06B6D4

## Concepts
- Why one memory type isn't enough (animated "human memory" analogy)
- Tier 1: Working Memory — scratchpad for current task state
- Tier 2: Episodic Memory — vector DB of past interactions
- Tier 3: Procedural Memory — skill library of learned tool sequences
- Summarization pipeline: compressing long conversations
- Memory compaction and cross-session persistence
- Visual: Animated brain diagram showing memory tiers activating

## Hands-On Lab
Build a 3-tier memory system: working memory (dict), episodic memory (ChromaDB of past conversations), procedural memory (JSON of learned UCC entity resolution patterns). Test persistence across sessions.

## Quiz Focus (5 questions)
1. Why not just use RAG for everything? (RAG is retrieval, not all memory is documents)
2. What goes in working memory? (current task state, intermediate results)
3. What goes in episodic memory? (summaries of past interactions for similar case lookup)
4. Do you always need all three tiers? (no — start with working memory, add others as needed)
5. What are privacy concerns with episodic memory? (storing user interactions requires consent, data retention policies)
