# M03 Lab: Prompts

> Build a code-review assistant three ways: a structured system prompt, a comparison of zero-shot / few-shot / chain-of-thought patterns, and a multi-turn `ConversationManager`.

## Prerequisites

- M01 complete (Ollama serving `mistral`, `openai` SDK installed)

## Exercises

| Step | File | What You Build | Key Concept |
|------|------|---------------|-------------|
| 1 | `review_agent.py` / `.js` | Code reviewer with a sectioned system prompt | System prompt = role + constraints + output format + tone |
| 2 | `pattern_compare.py` / `.js` | Same review, three prompt patterns | Zero-shot vs few-shot vs chain-of-thought |
| 3 | `review_conversation.py` / `.js` | Multi-turn review session | `ConversationManager`, growing input tokens |

## Step 1: Code Review System Prompt

**File:** `starter/review_agent.py` (or `.js`)

Write `REVIEW_SYSTEM_PROMPT` with four labeled sections — `<role>`, `<review_criteria>`, `<output_format>`, `<tone>` — then send the provided SQL-injection test snippet for review.

**Success check:** the response uses your `## Category` headings AND flags the f-string SQL injection. If Mistral misses the injection, sharpen `<review_criteria>` (e.g., name "injection risks" explicitly) and re-run — that feedback loop *is* the lesson.

## Step 2: Compare Prompt Patterns

**File:** `starter/pattern_compare.py` (or `.js`)

The buggy `process_items` snippet is provided. Build three prompts:
- **zero-shot** — just "Review this code"
- **few-shot** — two example reviews first, then the code
- **chain-of-thought** — "review step by step: 1. bugs 2. performance 3. style 4. summarize"

Print each response and its token usage. **What to observe:** few-shot mimics your example format; CoT catches more issues (like `!= None` → `is None` and the unnecessary `range(len(...))`) but costs ~2-3× the output tokens.

## Step 3: Multi-Turn Review Conversation

**File:** `starter/review_conversation.py` (or `.js`)

Implement `ConversationManager.send()`:
1. Append the user message to `self.messages`
2. Call the API with `[system] + self.messages`
3. Append the assistant reply, return `(text, usage)`
4. **On error: pop the user message** before re-raising — a failed call must not corrupt history

The provided 5-turn script reviews code, asks for fixes, and prints cumulative token usage. **What to observe:** `prompt_tokens` grows every turn — you resend the whole history each time.

## Verify Everything Works

```bash
python starter/review_agent.py && python starter/pattern_compare.py && python starter/review_conversation.py
```

## Stretch Goals

- Add a `max_history` parameter to `ConversationManager` that drops oldest turns past N messages (preview of M08)
- Make the reviewer respond in JSON and parse it (preview of M04)
