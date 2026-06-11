# M11 Lab: Multi-Layer Memory

> One memory is not enough. You'll build the two workhorse layers — a token-aware `BufferMemory` (this session) and a persistent `VectorMemory` (across sessions) — then compose them into one `AgentMemory.build_context()` call.

## Prerequisites

- M09 complete (ChromaDB installed and understood)
- Dependencies: `pip install openai chromadb`

> **Scope note:** Python is the full lab. In Node.js, the vector layer requires a Chroma server, so the JS lab covers `BufferMemory` only — the semantic layer pattern is identical (see the course HTML's `vectorMemory.js`). Layer 3 (episodic/summary memory) is a stretch goal; the course HTML has the complete `EpisodicMemory` class.

## Exercises

| Step | File | What You Build | Key Concept |
|------|------|---------------|-------------|
| 1 | `buffer_memory.py` / `.js` | Sliding window with token budget | Pair-wise eviction, write-time enforcement |
| 2 | `vector_memory.py` | Persistent semantic store | Dedup on save, similarity recall, ChromaDB persistence |
| 3 | `agent_memory.py` | The facade | `build_context()` assembly order |

## Step 1: BufferMemory

Implement `add(role, content)`:
- Append, then evict from the FRONT while over `max_messages`
- Then evict while `_estimate_tokens() > max_tokens`
- **Always evict in PAIRS (user + assistant)** — orphaned turns confuse instruction-tuned models
- `_estimate_tokens` is provided (4-chars-per-token heuristic — good enough for eviction)

## Step 2: VectorMemory

ChromaDB `PersistentClient` — memories survive restarts. Implement:
- `save(text, metadata)`: **dedup first** (query for nearest existing memory; if cosine similarity ≥ 0.95, return the existing ID instead of saving a duplicate), then `collection.add()` with a UUID. Metadata values must be flat str/int/float/bool — ChromaDB rejects nested objects.
- `recall(query, k)`: query, convert ChromaDB's cosine *distance* to similarity (`sim = 1 - distance`), return `[{id, text, score, metadata}]` sorted by score.

## Step 3: AgentMemory Facade

Implement `build_context(query)` — assembly order is the whole lesson:
1. `[system]` relevant vector memories (only hits with score ≥ 0.5), formatted as a `[RELEVANT PAST FACTS]` block
2. Buffer messages last (most recent = highest priority — the buffer always wins over older context)

And `save_turn(user_msg, assistant_msg)`: add both to the buffer; if the exchange contains facts worth keeping (the provided heuristic: any message > 80 chars), save a condensed line to vector memory.

## Run It

```bash
python starter/buffer_memory.py     # smoke test: eviction behavior
python starter/vector_memory.py     # smoke test: save/dedup/recall
python starter/agent_memory.py      # 2-session demo (see below)
```

**The 2-session demo** in `agent_memory.py` is the payoff: session 1 tells the agent "Order TRK-001 shipped via FedEx; customer prefers email." Session 2 starts a FRESH buffer (process restart simulated), asks "How should I notify the customer about their delivery?" — and the agent answers with FedEx + email because `build_context()` recalled both facts from the persistent vector store.

## Stretch Goals

- Add Layer 3: port `EpisodicMemory` from the course HTML (compress sessions to structured JSON episodes with Mistral)
- Add `forget(memory_id)` cleanup and an expiry policy (delete memories older than N days)
- Replace the chroma built-in embedder with `sentence-transformers/all-MiniLM-L6-v2` as in the course
