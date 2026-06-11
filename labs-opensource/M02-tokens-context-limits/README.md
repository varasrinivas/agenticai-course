# M02 Lab: Tokens & Context Limits

> Local models are free per token, but every token still costs **latency** and **context space**. You'll count tokens, build a prompt budget that auto-truncates, and benchmark your machine's real tokens-per-second.

## Prerequisites

- M01 complete
- Extra dependency:
  ```bash
  pip install tiktoken        # Python
  npm install js-tiktoken     # Node.js (already in package.json)
  ```

## Exercises

| Step | File | What You Build | Key Concept |
|------|------|---------------|-------------|
| 1 | `token_counting.py` / `.js` | Token counter with chat overhead | BPE tokenization, per-message overhead |
| 2 | `prompt_budget.py` / `.js` | `PromptBudget` class with auto-truncation | Context window management |
| 3 | `token_timer.py` / `.js` | Throughput benchmark | Tokens/second = your real cost |

> **Why cl100k_base?** Mistral uses its own SentencePiece tokenizer, but `tiktoken`'s `cl100k_base` encoding is within a few percent for English text and needs no model download. Good enough for budgeting. (Stretch goal: compare against the exact Mistral tokenizer via `transformers`.)

## Step 1: Count Tokens

**File:** `starter/token_counting.py` (or `.js`)

You will:
1. Encode sample strings with `cl100k_base` and print token counts (the samples are chosen to surprise you — "tokenization" is 2 tokens, "ChatGPT" is 1)
2. Implement `count_chat_tokens(messages)` — a full chat request costs more than the sum of its strings: ~4 tokens of overhead per message (role + content markers) plus ~3 tokens of reply primer

```bash
python starter/token_counting.py    # or: node starter/token_counting.js
```

## Step 2: The PromptBudget Class

**File:** `starter/prompt_budget.py` (or `.js`)

The class skeleton and a 4-turn demo conversation are provided. You implement:

- `remaining(messages, tools, reserve_output)` — how many tokens are left after counting messages + tool definitions and reserving room for the model's reply
- `fits(text, messages, ...)` — would adding `text` as a new message still fit?
- `truncate_history(messages, ...)` — drop the **oldest non-system** messages until the conversation fits; never drop the system prompt; return a new list (don't mutate)

The demo loop calls your methods before every API call and prints `Tokens remaining: N` each turn.

## Step 3: TokenTimer Benchmark

**File:** `starter/token_timer.py` (or `.js`)

You implement `TokenTimer.run(messages, max_tokens)`: time the API call, then compute `decode_tokens_per_sec = completion_tokens / elapsed`. The provided benchmark warms up the model first (cold start would pollute the numbers), then tests ~100/500/1000-token prompts and prints a table.

**What you learn:** your machine's real throughput. CPU-only ≈ 5–15 tok/s; Apple Silicon ≈ 25–60; NVIDIA GPU ≈ 40–100+.

## Verify Everything Works

```bash
python starter/token_counting.py && python starter/prompt_budget.py && python starter/token_timer.py
```

## Stretch Goal

Install `transformers` and compare `cl100k_base` counts against the exact Mistral tokenizer (`mistralai/Mistral-7B-v0.1`). For typical English text the difference is under 10% — see the module HTML for the comparison script.
