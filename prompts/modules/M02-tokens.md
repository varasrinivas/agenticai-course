# M02: Tokens — The Atoms of AI Communication

**Track**: 1 — Foundations | **Position**: 2 of 30 | **Level**: Beginner
**Prerequisites**: M01
**Estimated Time**: 40-50 minutes
**Track Color**: var(--track-foundations) / #6366F1

## Concepts to Cover

### 1. What Are Tokens?
- Analogy: "Tokens are like syllables, but for AI. The word 'understanding' might be 2 tokens: 'understand' + 'ing'. The word 'cat' is 1 token. An emoji might be 2-3 tokens."
- Technical: Byte-pair encoding (BPE) — the algorithm that splits text into subword units. Each token maps to a numeric ID. Claude's vocabulary is ~100K tokens.
- Animation: `TOKEN_FLOW` — Interactive tokenizer. Learner types any text → see it split into colored blocks in real-time. Each block shows the token text + its numeric ID. Different words get different colors. Show that common words = 1 token, rare words = multiple tokens.
- This is the module's hero interactive element. Must feel snappy and fun.

### 2. Why Tokens Matter
- Three reasons: COST (you pay per token), LIMITS (context window is measured in tokens), PERFORMANCE (more tokens = slower + more expensive)
- Show pricing: Input tokens vs output tokens, with real Claude pricing
- Animation: A simple cost calculator — learner enters a conversation length, sees estimated cost

### 3. Context Window
- Analogy: "Your desk can only fit so many papers. The context window is Claude's desk. Everything — your system prompt, conversation history, the current message, AND Claude's response — has to fit on the desk."
- Technical: Claude's context windows (model comparison). Fixed size. What happens when you exceed it (truncation, not graceful degradation).
- Animation: `CONTEXT_WINDOW` — A rectangular area representing the window. As conversation messages appear, they fill the space. When full, oldest messages start fading. Show the allocation: [system prompt | conversation history | user message | response space]
- Key insight: Token budget management is a CORE agent engineering skill. This will be expanded in M08.

### 4. Token Counting in Practice
- Using `anthropic.count_tokens()` or tiktoken
- Building a token budget: "How much room do I have for the response?"
- Common mistake: Forgetting that the response ALSO uses tokens from the context window budget

## Code Walkthrough
- Token counting with the Anthropic SDK
- Building a simple token budget calculator function
- Demonstrating context window overflow and how to detect it

## Hands-On Exercise
- Build a token-aware prompt function that:
  1. Counts tokens in the system prompt
  2. Counts tokens in conversation history
  3. Calculates remaining budget for response
  4. Warns if budget is low
- Stretch: Build a conversation that deliberately fills the context window and observe what happens

## Quiz Focus
- How many tokens is "Hello, how are you?" (approximately)
- Why are output tokens more expensive than input tokens?
- What happens when you exceed the context window?
- Token budget allocation question (given a scenario, calculate available response tokens)
- Which of these strategies helps manage token budget? (multiple select)
