# M04: Structured Output & Parsing

**Track**: 1 — Foundations | **Position**: 4 of 30 | **Level**: Beginner → Intermediate
**Prerequisites**: M01-M03
**Estimated Time**: 50-60 minutes
**Track Color**: var(--track-foundations) / #6366F1

## Concepts
- Why agents need structured responses (JSON, XML, tool-use format)
- Claude's native tool use / function calling — how it guarantees structure
- Animated: The "restaurant menu" analogy — tools as menu items Claude picks from
- JSON mode, stop sequences, and output validation
- Pydantic/Zod schemas for response validation
- Error recovery: What happens when parsing fails?
- Visual: Animated flow from natural language → structured JSON → application state

## Hands-On Lab
Build a structured data extraction pipeline that takes freetext UCC filing descriptions and extracts: debtor name, secured party, collateral type, filing date into validated JSON.

## Quiz Focus (5 questions)
1. How does tool_use guarantee structured output? (returns JSON matching the schema)
2. What's the difference between asking for JSON in the prompt vs tool_use? (tool_use is guaranteed, prompt-based can fail)
3. What does Pydantic do? (validates response matches expected schema)
4. What should your code do if parsing fails? (retry with clarification, or fallback)
5. tool_use guarantees structure but not ___? (semantics — the values could be wrong)
