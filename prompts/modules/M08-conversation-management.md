# M08: Conversation Management

**Track**: 3 — Memory & Context | **Position**: 8 of 30 | **Level**: Intermediate
**Prerequisites**: M01-M04
**Estimated Time**: 50-60 minutes
**Track Color**: var(--track-memory) / #06B6D4

## Concepts
- The stateless reality: Claude has NO memory between API calls
- Conversation history management: full history, sliding window, summarization
- Token budget allocation: system prompt + history + user message + response
- Interactive: Token budget calculator with draggable allocation sliders
- Message pruning strategies — what to keep, what to drop
- Visual: Animated "memory palace" showing conversation state management

## Hands-On Lab
Build a conversation manager that: (1) maintains full history, (2) switches to sliding window at 80% context, (3) auto-summarizes old messages. Test with 20+ turn UCC research conversations.

## Quiz Focus (5 questions)
1. Does Claude remember previous conversations? (no — stateless between calls)
2. What is a sliding window? (keep last N messages, drop oldest)
3. When should you summarize vs truncate? (summarize when old context matters)
4. What happens if you exceed the context window? (API error or truncation)
5. How do you allocate token budget? (system prompt first, then history, then user message, leave room for response)
