# M01 Lab: The LLM Mental Model

> Four small experiments that build your intuition for how a local LLM behaves: it predicts tokens, it's steered by system prompts, temperature controls randomness, and every token costs time.

## Prerequisites

- M00 complete (Ollama serving `mistral`, `openai` SDK installed)

## Exercises

| Step | File | What You Build | Key Concept |
|------|------|---------------|-------------|
| 1 | `first_call.py` / `.js` | First chat completion | Request/response anatomy, `choices[0].message.content` |
| 2 | `system_prompts.py` / `.js` | Same question, three personas | System prompt = personality programming |
| 3 | `temperature.py` / `.js` | Same prompt at temp 0.0 vs 1.0, ×3 runs | Sampling and (non-)determinism |
| 4 | `token_usage.py` / `.js` | Usage metrics for 3 prompt sizes | `prompt_tokens` / `completion_tokens` |
| 5 (stretch) | `chat_cli.py` / `.js` | Interactive CLI chat with history | Conversation = resending all messages |

## Step 1: First API Call

**File:** `starter/first_call.py` (or `.js`)

Make a single `client.chat.completions.create()` call with a system message and the question *"What is a large language model? Explain in 2 sentences."* Print the answer and token usage.

```bash
python starter/first_call.py    # or: node starter/first_call.js
```

## Step 2: System Prompt Experiment

**File:** `starter/system_prompts.py` (or `.js`)

Ask the **same question** ("What is the moon?") with three different system prompts: pirate, formal academic, haiku-only. The user message never changes — only the system message. Watch the answers transform.

**The key line you must get right:** the system prompt goes in the `messages` array as `{"role": "system", ...}` — sending the same messages three times with no system entry produces three identical-ish answers and proves nothing.

## Step 3: Temperature Experiment

**File:** `starter/temperature.py` (or `.js`)

Run *"Write a one-sentence description of the moon."* three times at `temperature=0.0` and three times at `temperature=1.0`.

**What you should observe:** temp 0.0 produces (nearly) identical sentences; temp 1.0 produces three different ones. Note for local models: Ollama's temp-0 is *mostly* deterministic, not perfectly — tiny numeric differences can flip a token.

## Step 4: Token Usage

**File:** `starter/token_usage.py` (or `.js`)

Send three prompts of increasing size and print `usage.prompt_tokens`, `usage.completion_tokens`, and the total for each. There is no dollar cost locally — but every token is **latency**: at ~10 tokens/s on CPU, a 500-token answer takes ~50 seconds.

## Step 5 (Stretch): CLI Chat

**File:** `starter/chat_cli.py` (or `.js`)

Build a terminal chat loop that keeps a `conversation` list and resends the **entire history** every turn. Type `quit` to exit. Gotcha handled in the solution: if the API call fails, pop the user message you just appended so history stays consistent.

## Verify Everything Works

```bash
# Python
python starter/first_call.py && python starter/system_prompts.py && python starter/temperature.py && python starter/token_usage.py

# Node.js
node starter/first_call.js && node starter/system_prompts.js && node starter/temperature.js && node starter/token_usage.js
```

Compare with `expected_output/sample_output.txt`.
