# M08 Lab: Conversation Management

> The model is stateless — every "conversation" is your code resending history. You'll build three managers of increasing intelligence: full-history, sliding-window, and auto-summarizing with save/restore.

## Prerequisites

- M03 complete (you built a basic ConversationManager there)

## Exercises

| Step | File | What You Build | Key Concept |
|------|------|---------------|-------------|
| 1+2 | `conversation_manager.py` / `.js` | Full-history manager + `SlidingWindowManager` subclass | Token tracking, windowed history, role alternation |
| 3 | `smart_manager.py` / `.js` | `SmartConversationManager` | Auto-summarization on token threshold, JSON persistence |

## Step 1: Basic ConversationManager with Token Tracking

**File:** `starter/conversation_manager.py` (or `.js`)

Implement `send()`: append the user message, call the API with `[system] + messages`, accumulate `usage.prompt_tokens` / `completion_tokens` into running totals, append the reply, return it. On failure: pop the user message and re-raise. (Same as M03, plus the token accounting.)

**Run the test harness and watch `total_input` grow superlinearly** — each turn resends everything.

## Step 2: SlidingWindowManager

Same file. Subclass that overrides only `get_messages()`:
- Keep all messages in storage, but return system + only the **last N**
- **Role-alternation gotcha**: if the window starts with an `assistant` message, drop it — history sent to the API should start with a `user` turn

The harness asks 6 questions with `window_size=6`, then proves storage (12 messages) ≠ sent (6 messages).

## Step 3: SmartConversationManager

**File:** `starter/smart_manager.py` (or `.js`)

The summarization threshold check, `save()`, and `load()` are provided. You implement `_summarize_old_messages()`:
1. Keep the last `recent_turns_to_keep * 2` messages verbatim
2. Send the OLDER messages to Mistral with a summary prompt ("Preserve: key decisions, user preferences, important facts. Skip: greetings, filler.")
3. If a summary already exists, chain it: `"Previous context: {old}\n\nRecent: {new}"`
4. Replace history with: `[summary-as-user-msg, "Understood." assistant msg, *recent]`
5. **On summarization failure, fall back to plain truncation** — never crash the conversation

Then implement the trigger inside `send()`: after a successful reply, if `last_input_tokens > token_threshold`, summarize.

The harness uses a deliberately low threshold (3,000 tokens) so you can watch the summarization fire within a few verbose turns, then `save()` → `load()` → "Where were we?" proves persistence.

## Verify

```bash
python starter/conversation_manager.py && python starter/smart_manager.py
```

## Stretch Goals

- Track summarization "information loss": ask a question about a summarized-away detail and see if the model still knows
- Add `max_file_size` rotation to `save()` (preview of production logging in M19)
