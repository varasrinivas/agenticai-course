# M08 Lab: Conversation Management

> **Claude is stateless. Every API call is a blank slate. YOUR code is the memory.**

Claude does not remember previous messages. Each `messages.create()` call starts
from scratch. If you want a multi-turn conversation, you must send the full
message history every time. This lab teaches you three strategies for managing
that history as it grows: full history, sliding window, and auto-summarization.

## Prerequisites

- Python 3.10+ or Node.js 18+
- Anthropic API key in `.env` file (`ANTHROPIC_API_KEY=sk-ant-...`)
- Install dependencies:
  ```bash
  # Python
  pip install anthropic python-dotenv

  # Node.js
  npm install @anthropic-ai/sdk dotenv
  ```

## Exercises

| Step | File | What You Build | Key Concept |
|------|------|---------------|-------------|
| 1 | `full_history.py` / `full_history.js` | Chat agent that maintains full conversation history | Message list management, role alternation, token counting |
| 2 | `sliding_window.py` / `sliding_window.js` | Sliding window conversation manager with token budget | Token counting, window sizing, context budget allocation |
| 3 | `auto_summarize.py` / `auto_summarize.js` | Auto-summarizing conversation manager that compresses old messages | Summarization pipeline, context preservation, 80% threshold |

## Step 1: Full Conversation History

**File:** `starter/full_history.py` (or `.js`)

You will:
1. Build a `ConversationManager` class that stores messages with proper role alternation
2. Implement `add_user_message(text)` to append a user message
3. Implement `send()` to call the Claude API with full history and append the response
4. Implement `get_history()` and `get_token_count()` to inspect conversation state
5. Token counting uses `len(str(messages)) // 4` as a simple estimator

**System prompt:** "You are a UCC filing research assistant. Help users understand UCC filings, lien risks, and secured transactions."

**Test with a 5-turn conversation about UCC filings:**
1. "What is a UCC-1 filing?"
2. "How long does a UCC-1 last before it lapses?"
3. "What happens when a filing lapses?"
4. "Can a filing be renewed?"
5. "Summarize everything we discussed"

**Run it:**
```bash
python starter/full_history.py
# or
node starter/full_history.js
```

## Step 2: Sliding Window with Token Budget

**File:** `starter/sliding_window.py` (or `.js`)

You will:
1. Build a `SlidingWindowManager` class with a configurable `max_tokens` budget (default 4096)
2. Implement `_estimate_tokens(messages)` to count approximate tokens
3. Implement `_trim_history()` that drops the oldest messages when over budget (keeping the system prompt and most recent messages)
4. Log when messages are dropped: `[WINDOW] Dropped N oldest messages (X tokens freed)`

**Test with 10+ rapid-fire questions that force the window to slide.**

**Run it:**
```bash
python starter/sliding_window.py
# or
node starter/sliding_window.js
```

## Step 3: Auto-Summarization

**File:** `starter/auto_summarize.py` (or `.js`)

You will:
1. Build an `AutoSummarizeManager` class that monitors token usage
2. At 80% of budget, trigger a summarization step
3. Summarization sends oldest messages to Claude with "Summarize this conversation so far in 2-3 sentences"
4. Replace old messages with a single system-injected summary message
5. Log: `[SUMMARIZE] Compressed N messages into summary (X tokens -> Y tokens)`
6. Keep recent messages untouched

**Test with a 15+ turn conversation that triggers summarization.**

**Run it:**
```bash
python starter/auto_summarize.py
# or
node starter/auto_summarize.js
```

## Verification

After completing all three steps, run the solutions to see expected behavior:

```bash
# Python
python solution/full_history.py
python solution/sliding_window.py
python solution/auto_summarize.py

# Node.js
node solution/full_history.js
node solution/sliding_window.js
node solution/auto_summarize.js
```

Compare your output against `expected_output/sample_output.txt`.

## What You Built

By completing this lab, you have implemented:

1. **Full history management** -- the foundational pattern for multi-turn conversations
2. **Token counting** -- estimating how much context you are consuming per turn
3. **Sliding window** -- a simple strategy to cap memory usage by dropping old messages
4. **Auto-summarization** -- an intelligent strategy that compresses old context instead of discarding it
5. **Context budget awareness** -- the skill of knowing when your conversation is running out of room

These patterns are critical for any production agent that has long-running conversations.

## Next

- **M09**: RAG -- Retrieval-Augmented Generation
- **M10**: Agent Architecture Patterns
