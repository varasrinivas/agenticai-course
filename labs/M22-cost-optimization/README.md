# M22 Lab: Cost Optimization

> Sending every query to the biggest model is like hiring a brain surgeon to put on a band-aid. **Route smart, cache aggressively, compress ruthlessly.**

In this lab you add caching, model routing, token optimization, and cost tracking to the UCC filing agent. By the end, the same workload runs at ~70% less cost with no loss in answer quality.

## Prerequisites

- Python 3.10+ or Node.js 18+
- Completed M02 (tokens), M12 (ReAct agent), M21 (deployment basics)
- No external caching libraries needed — you build everything from scratch
- Install dependencies:
  ```bash
  # Python
  pip install anthropic python-dotenv

  # Node.js
  npm install @anthropic-ai/sdk dotenv
  ```

## Exercises

| Step | Time | File | What You Build | Key Concept |
|------|------|------|---------------|-------------|
| 1 | 10 min | `response_cache.py` | Hash-based response cache with TTL and LRU eviction | Cache key normalization, TTL expiry, hit-rate tracking |
| 2 | 15 min | `model_router.py` | Complexity-based model router (Haiku/Sonnet/Opus) | Task classification, cost-aware routing rules |
| 3 | 10 min | `token_optimizer.py` | System prompt compressor and message window optimizer | Token estimation, prompt compression, sliding window |
| 4 | 10 min | `cost_tracker.py` | Per-call cost tracker with savings analysis | Cost accounting, baseline comparison, reporting |
| 5 | 10 min | `optimized_agent.py` | Full optimization pipeline composing all four components | Pipeline composition, batch processing, A/B comparison |

## Step 1: Build the Response Cache (10 min)

**File:** `starter/response_cache.py` (or `.js`)

You will:
1. Build a `ResponseCache` class that hashes queries into cache keys using SHA-256
2. Implement TTL-based expiration (default 300 seconds)
3. Implement LRU eviction when the cache exceeds `max_entries`
4. Normalize queries (lowercase, strip whitespace, sort params) for better hit rates
5. Track cache statistics: hits, misses, hit rate, eviction count

**Run it:**
```bash
python starter/response_cache.py
# or
node starter/response_cache.js
```

**Checkpoint:** Self-test passes showing cache hits, misses, TTL expiry, and LRU eviction. Hit rate should be > 0%.

## Step 2: Build the Model Router (15 min)

**File:** `starter/model_router.py` (or `.js`)

You will:
1. Define real Claude model pricing (Haiku, Sonnet, Opus) per 1M tokens
2. Build keyword-based task classification: filing lookups go to Haiku, entity resolution to Sonnet, risk analysis to Opus
3. Implement `route()` that returns the model name, reason, and cost info
4. Implement `estimate_cost()` to calculate actual dollar cost for a given call

**Run it:**
```bash
python starter/model_router.py
# or
node starter/model_router.js
```

**Checkpoint:** Filing lookups route to Haiku, risk analyses route to Opus, and each routing decision includes a human-readable reason.

## Step 3: Build the Token Optimizer (10 min)

**File:** `starter/token_optimizer.py` (or `.js`)

You will:
1. Compress system prompts by removing redundant whitespace and abbreviating common phrases
2. Implement a sliding-window message optimizer that keeps only the N most recent messages
3. Track original vs. optimized token counts and calculate reduction percentage

**Run it:**
```bash
python starter/token_optimizer.py
# or
node starter/token_optimizer.js
```

**Checkpoint:** System prompt compression achieves at least 25% token reduction. The optimizer reports before/after counts.

## Step 4: Build the Cost Tracker (10 min)

**File:** `starter/cost_tracker.py` (or `.js`)

You will:
1. Record every API call with model, token counts, and cache status
2. Calculate total cost using real model pricing
3. Compare actual cost against an all-Sonnet baseline (what you would have spent without routing)
4. Generate a formatted cost report

**Run it:**
```bash
python starter/cost_tracker.py
# or
node starter/cost_tracker.js
```

**Checkpoint:** The report shows total cost, per-model breakdown, cache savings, and routing savings vs. baseline.

## Step 5: Wire the Optimization Pipeline (10 min)

**File:** `starter/optimized_agent.py` (or `.js`)

You will:
1. Compose all four components into an `OptimizedAgent` class
2. Implement the full pipeline: cache check -> route -> optimize tokens -> execute (mock) -> track cost -> cache response
3. Add batch processing for non-time-sensitive workloads
4. Run a side-by-side cost comparison: baseline vs. optimized

**Run it:**
```bash
python starter/optimized_agent.py
# or
node starter/optimized_agent.js
```

**Checkpoint:** The comparison shows ~70% cost reduction over 20 queries. Cached queries cost $0.00.

## Verification

After completing all exercises, run the solutions to see expected behavior:

```bash
# Python
python solution/optimized_agent.py

# Node.js
node solution/optimized_agent.js
```

Compare your output against `expected_output/optimization_report.txt`.

## Key Takeaways

1. **Cache first** — Identical queries should never hit the API twice
2. **Route by complexity** — Simple lookups don't need the most expensive model
3. **Compress tokens** — Every token you don't send is money you don't spend
4. **Measure everything** — You can't optimize what you don't track
5. **Batch when possible** — The Batch API gives 50% discount for non-urgent work
