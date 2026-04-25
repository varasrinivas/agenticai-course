# M03: Prompts — Programming in Natural Language

**Track**: 1 — Foundations | **Position**: 3 of 30 | **Level**: Beginner
**Prerequisites**: M01, M02
**Estimated Time**: 50-60 minutes
**Track Color**: var(--track-foundations) / #6366F1

## Concepts
- Anatomy of a prompt: system, user, assistant roles (visual message flow)
- Prompt engineering patterns: zero-shot, few-shot, chain-of-thought (animated comparison)
- Role prompting, structured output requests (XML/JSON), delimiters
- The "prompt → completion" loop animated end-to-end
- System prompts as "personality programming" — interactive builder
- Visual: Animated message stack showing how Claude sees the conversation

## Hands-On Lab
Build a multi-turn conversation manager with system prompt, few-shot examples, and chain-of-thought reasoning. Test with UCC domain questions.

## Quiz Focus (5 questions)
1. What are the three message roles in Claude's API? (system, user, assistant)
2. When should you use few-shot vs zero-shot? (few-shot when format matters)
3. What does chain-of-thought prompting do? (forces step-by-step reasoning)
4. Why put instructions in the system prompt? (persists across turns, sets behavior)
5. What happens if your system prompt exceeds the context window? (truncation or error)
