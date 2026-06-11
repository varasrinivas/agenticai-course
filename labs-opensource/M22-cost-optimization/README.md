# M22 Lab: Cost Optimization

> Local models bill you in seconds, not dollars. The two highest-leverage optimizations: **don't run inference you've already run** (two-layer response cache) and **measure before you choose a model** (benchmark harness).

## Prerequisites

- M09/M11 complete (ChromaDB)
- `pip install openai chromadb httpx`

## Files

| File | Status | What It Is |
|------|--------|------------|
| `agent_cache.py` | **TODOs** | Two-layer cache: exact-match dict + semantic ChromaDB, both with TTL |
| `agent_benchmark.py` | Complete | 20-prompt benchmark harness → CSV + Markdown report |

> Python is the full lab (the semantic layer needs in-process ChromaDB). The course HTML has the TypeScript benchmark and prompt-efficiency mirrors.

## Part 1: AgentCache

**Layer 1** — exact match: `sha256(f"{model}:{query}")` → `CacheEntry(response, created_at, ttl_s)`. Free, instant, but misses paraphrases.
**Layer 2** — semantic: ChromaDB stores the response with the query embedded; a NEW query that's ≥0.95 cosine-similar hits the cache. *"Who is the debtor on UCC-1 #12345?"* hits the entry cached for *"What is the debtor name in UCC filing #12345?"*

You implement:
- `get(query)`: purge expired Layer-1 entries → exact lookup → semantic lookup (similarity = `1 - distance`; check `expires_at` in metadata) → None
- `set(query, response, ttl_s)`: write BOTH layers; Layer-2 failures are swallowed (Layer 1 is sufficient fallback)
- `infer(query)`: cache check → on miss, call Mistral, cache the result, count stats

**Threshold judgment call:** 0.95 is conservative. Lower it and you serve wrong-but-similar answers; raise it and the semantic layer never fires. The smoke test prints which layer answered each query so you can feel the tradeoff.

## Part 2: Benchmark Harness (run it, study it)

`agent_benchmark.py` runs 20 entity-resolution prompts (extraction, classification, JSON, reasoning, edge cases) against each model in `MODELS`, measures p50/p95 latency and tokens/sec from Ollama's own `eval_count`/`eval_duration`, has a second model judge correctness 1–10, and writes `benchmark_results.csv` + `.md`.

Default `MODELS = ["mistral"]`. Pull a competitor and compare:
```bash
ollama pull phi3:mini
# edit MODELS = ["phi3:mini", "mistral"]
python starter/agent_benchmark.py
```

**The decision rule from the module:** pick the SMALLEST model whose quality clears your bar — a 3.8B model at 2× the speed beats a 7B model your users won't wait for.

## Run It

```bash
python starter/agent_cache.py       # cache smoke test (3 queries, 1 Ollama call)
python starter/agent_benchmark.py   # ~20 prompts × N models; minutes on CPU
```

## Stretch Goals

- Try quantization variants: `ollama pull mistral:7b-instruct-q4_K_M` vs `q8_0` — benchmark both; Q4 is ~2× faster at ~3% quality loss for most agent tasks
- Add cache metrics to the M20 drift detector (hit rate is a driftable metric!)
- Implement prompt-efficiency technique #3 from the course: truncate tool results to 500 chars before they enter history
