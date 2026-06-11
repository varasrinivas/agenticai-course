# M03B Lab: Context Engineering — The Poisoned Transcript

> Prompt engineering optimizes *what you say*; context engineering optimizes *everything the model sees*. You'll build a `ContextBudget` class that accounts for all six context layers, then prove it works by fixing a "rotted" transcript.

## Prerequisites

- M02 complete (you understand tokens and budgets)
- Dependencies: `pip install openai tiktoken` / `npm install openai js-tiktoken`

## The Lab in One Sentence

Load a fixture conversation full of noise (retries, duplicate tool results, resolved detours), ask the model a question **twice** — once with the raw rotted context, once after summarize-and-crop — and measure the token and latency difference.

## Files

| File | Status | What It Is |
|------|--------|------------|
| `starter/context_budget.py` / `.js` | **TODOs** | The `ContextBudget` class — you implement 4 methods |
| `starter/poisoned_transcript.json` | Complete | Fixture: an order-tracking conversation with noise |
| `starter/diagnose.py` / `.js` | Complete | Runs the before/after comparison using YOUR class |

## What You Implement (in `context_budget`)

1. **`account()`** — return a per-layer token breakdown dict: `system`, `tools`, `retrieved`, `history`, `tool_results`, `current`. (`count_tokens` is provided.)
2. **`strategy()`** — map utilization (`total() / max_tokens`) to an action: `< 0.60 → "ok"`, `< 0.75 → "compress"`, `< 0.90 → "summarize"`, else `"critical"`.
3. **`crop()`** — apply the strategy in place: compress+ drops tool definitions; summarize+ keeps only the last 4 history turns (2 if critical) and last 2 tool results; critical also drops retrieved docs.
4. **`build_messages()`** — assemble `(system, messages)` with retrieved docs appended to the **current user message** (end position = highest recall on Mistral-7B), never the middle.

Provided complete: `count_tokens` (tiktoken), `MODEL_LIMITS`, `summarize_history` (a separate model call that compresses old turns while preserving IDs, amounts, and decisions), and `checkpoint()` which wires it in.

## Run It

```bash
cd starter
python diagnose.py        # or: node diagnose.js
```

**Expected shape of the output:**

```
=== Token Breakdown (rotted) ===
  system         : 41 tokens
  tools          : 62 tokens
  history        : 612 tokens
  ...
>>> Run 1: ROTTED context (no fix)
Tokens: 781 in, 54 out  (6.21s)
Answer: ...November 3rd...

>>> Run 2: COMPRESSED context (after checkpoint)
  Total after compression: 312 tokens
Tokens: 387 in, 49 out  (3.05s)
Answer: ...November 3rd...

Token delta:   -394 input tokens
Latency delta: -3.16s
```

**The success criterion:** Run 2 must still cite the correct delivery date and order ID — the summarizer's CRITICAL instruction preserved them — while spending materially fewer input tokens. If Run 2 loses the date, your summary prompt (or `keep_recent`) is too aggressive.

## Stretch Goals

- Add a 7th layer: scratchpad/plan text, and include it in `account()`
- Poison the transcript further (duplicate the tool results 5×) and watch `strategy()` escalate from `ok` → `compress` → `summarize`
- Swap `model="mistral"` for a smaller model (e.g. `gemma2`) in `summarize_history` — summarization doesn't need your best model
