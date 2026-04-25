# M02: Tokens — The Atoms of AI Communication — Lab

## What You'll Build

A **token-aware prompt toolkit** that counts tokens, estimates API costs, and manages context window budgets. By the end of this lab you will have three working utilities you can drop into any Claude-powered project:

1. **Token Counter** — measure how many tokens different text types consume
2. **Cost Estimator** — predict API costs before you send a single request
3. **Budget Manager** — track token usage across a conversation and trim messages when you approach the context window limit

---

## Prerequisites

| Requirement | Details |
|---|---|
| M01 completed | You should be comfortable making a basic Claude API call |
| Python 3.10+ | `python --version` to check |
| Node.js 18+ | Only needed for the Node.js solutions |
| Anthropic API key | Stored in a `.env` file as `ANTHROPIC_API_KEY` |

## Setup

```bash
# Navigate to the lab directory
cd labs/M02-tokens

# Install Python dependencies
pip install anthropic python-dotenv tiktoken

# (Optional) Install Node.js dependencies for JS solutions
npm install @anthropic-ai/sdk dotenv gpt-tokenizer
```

Create a `.env` file in the `M02-tokens/` directory (or the project root):

```
ANTHROPIC_API_KEY=sk-ant-...your-key-here...
```

> **Note on token counting:** The Anthropic SDK provides `client.count_tokens()` for exact Claude token counts. This lab also shows `tiktoken` with the `cl100k_base` encoding as a free, offline approximation. Tiktoken counts will be close but not identical to Claude's actual tokenizer.

---

## Step 1: Count Tokens in Different Text Types

**Goal:** Understand how different content types (plain text, code, JSON) tokenize differently.

**Starter file:** `starter/token_counter.py`

### Instructions

1. Open `starter/token_counter.py` and read through the predefined sample texts.
2. Complete the `count_tokens(text)` function — use `tiktoken` with the `cl100k_base` encoding.
3. (Bonus) Add a second implementation using `anthropic.Anthropic().count_tokens()` if you want exact Claude counts (requires an API key).

### Run

```bash
python starter/token_counter.py
```

### Expected Output

```
=== Token Counter ===

Text Type            | Characters | Tokens | Ratio
---------------------|------------|--------|------
Short sentence       |         44 |     10 |  4.4
Paragraph            |        312 |     58 |  5.4
Code snippet         |        275 |     98 |  2.8
JSON blob            |        198 |     68 |  2.9

Key insight: Code and structured data use MORE tokens per character than prose.
```

(Your exact numbers may vary slightly depending on the tokenizer.)

### Checkpoint

- [ ] You can explain why code uses more tokens per character than English prose
- [ ] You understand the difference between characters and tokens
- [ ] Your function returns an integer token count for any input string

### Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError: tiktoken` | Run `pip install tiktoken` |
| Token counts are 0 | Make sure you're calling `encoding.encode(text)` and returning `len()` of the result |
| Counts don't match the sample output exactly | That's expected — different tokenizers produce different counts |

---

## Step 2: Build a Cost Estimator

**Goal:** Predict API costs before making requests so you can budget effectively.

**Starter file:** `starter/cost_estimator.py`

### Instructions

1. Open `starter/cost_estimator.py` and review the pricing constants.
2. Complete the `estimate_cost(input_tokens, output_tokens, model)` function.
3. The function should return a dict with `input_cost`, `output_cost`, `total_cost`, and `model`.
4. Run the main block to see cost estimates for three scenarios.

### Run

```bash
python starter/cost_estimator.py
```

### Expected Output

```
=== Cost Estimator ===

Model: claude-haiku
  Short query   (100 in / 200 out):   $0.000275
  Medium query  (1000 in / 2000 out): $0.002750
  Batch of 1000 (1000 queries):       $2.750000

Model: claude-sonnet
  Short query   (100 in / 200 out):   $0.003300
  Medium query  (1000 in / 2000 out): $0.033000
  Batch of 1000 (1000 queries):       $33.000000

Cost comparison:
  Sonnet is 12.0x more expensive than Haiku for the same workload.
  For 10,000 queries/day, Haiku = $27.50/day, Sonnet = $330.00/day.
```

### Checkpoint

- [ ] You can calculate cost given input tokens, output tokens, and a model
- [ ] You understand why choosing the right model matters for cost
- [ ] You can estimate daily/monthly costs for a production workload

### Troubleshooting

| Problem | Fix |
|---|---|
| Costs show as 0.0 | Make sure you're dividing by 1,000,000 (pricing is per million tokens) |
| KeyError on model name | Check that your pricing dict keys match the model strings exactly |

---

## Step 3: Build a Context Window Budget Manager

**Goal:** Track cumulative token usage across a conversation and prevent context window overflow.

**Starter file:** `starter/budget_manager.py`

### Instructions

1. Open `starter/budget_manager.py` and review the `ContextBudgetManager` class skeleton.
2. Implement `add_message()` — tokenize the content, store the message, return token info.
3. Implement `get_usage()` — return current, max, and remaining tokens.
4. Implement `would_fit()` — check whether a new text fits in the remaining budget.
5. Implement `trim_oldest()` — remove the oldest message(s) to free up space.
6. Run the main block to simulate a conversation approaching the context limit.

### Run

```bash
python starter/budget_manager.py
```

### Expected Output

```
=== Context Window Budget Manager ===

Adding messages to conversation...
  [1] user: "What is machine learning?" — 5 tokens (5 / 1000 used)
  [2] assistant: "Machine learning is a subset of AI..." — 42 tokens (47 / 1000 used)
  [3] user: "Can you give me an example?" — 7 tokens (54 / 1000 used)
  [4] assistant: "Sure! Consider email spam filtering..." — 89 tokens (143 / 1000 used)

Current usage: 143 / 1000 tokens (14.3%)
Remaining: 857 tokens

Would a 500-token message fit? True
Would a 900-token message fit? False

Simulating context overflow...
  Adding 5 large messages (200 tokens each)...
  Usage before trim: 1043 / 1000 tokens (104.3%) — OVER BUDGET
  Trimming oldest messages...
  Usage after trim: 843 / 1000 tokens (84.3%)
  Removed 2 messages to get back under budget.
```

(Token counts will vary; the demo uses a small 1000-token window for illustration.)

### Checkpoint

- [ ] Your manager tracks cumulative token usage
- [ ] `would_fit()` correctly predicts whether new content fits
- [ ] `trim_oldest()` removes messages until usage is under the max
- [ ] You understand why context window management matters for multi-turn agents

### Troubleshooting

| Problem | Fix |
|---|---|
| Token counts don't add up | Make sure `add_message` updates `self.total_tokens` |
| `trim_oldest` removes everything | Add a check to stop once usage is under `max_tokens` |
| `would_fit` always returns True | Compare `self.total_tokens + new_tokens` against `self.max_tokens` |

---

## Final Verification

Run all three scripts in sequence:

```bash
python starter/token_counter.py
python starter/cost_estimator.py
python starter/budget_manager.py
```

Or run the completed solutions:

```bash
python solution/token_counter.py
python solution/cost_estimator.py
python solution/budget_manager.py
```

Node.js solutions (ES modules):

```bash
node solution/token_counter.js
node solution/cost_estimator.js
node solution/budget_manager.js
```

All scripts should run without errors and produce output similar to the samples above.

---

## What You Built

| Utility | What It Does | Why It Matters |
|---|---|---|
| Token Counter | Measures token count for any text | Lets you predict costs and fit content into context windows |
| Cost Estimator | Calculates API cost by model | Prevents bill shock; informs model selection |
| Budget Manager | Tracks and manages context window usage | Essential for multi-turn agents that run long conversations |

These three utilities form the foundation of **token-aware agent design** — every production agent needs to understand its token budget.

---

## Next

**M03: Prompts — The Steering Wheel** — Learn prompt engineering patterns that make Claude do exactly what you need.
