# M11 Lab: Multi-Layer Memory Architecture

> One memory type isn't enough. Your agent needs short-term, long-term, and skill memory.

Real-world agents can't rely on a single context window. They need **working memory** for the current task, **episodic memory** to recall past experiences, and **procedural memory** to apply learned patterns. In this lab you build all three tiers and wire them into a single UCC research agent.

## Prerequisites

- Python 3.10+ or Node.js 18+
- Anthropic API key in `.env` file (`ANTHROPIC_API_KEY=sk-ant-...`)
- Install dependencies:
  ```bash
  # Python
  pip install anthropic python-dotenv chromadb

  # Node.js
  npm install @anthropic-ai/sdk dotenv chromadb
  ```

## Exercises

| Step | File | What You Build | Key Concept |
|------|------|---------------|-------------|
| 1 | `working_memory.py` / `working_memory.js` | Working memory scratchpad — key-value store for current task state | Task state, scratchpad pattern, structured working memory |
| 2 | `episodic_memory.py` / `episodic_memory.js` | Episodic memory — vector store of past conversations for similar case recall | ChromaDB, semantic similarity, conversation indexing |
| 3 | `memory_agent.py` / `memory_agent.js` | Full 3-tier memory agent — combines working + episodic + procedural memory | Memory orchestration, tier selection, cross-session persistence |

## Step 1: Working Memory Scratchpad

**File:** `starter/working_memory.py` (or `.js`)

You will:
1. Complete the `WorkingMemory` class with `set`, `get`, `delete`, `clear` methods
2. Implement `get_context()` — formats all working memory entries as a string for the system prompt
3. Implement `to_dict()` / `from_dict()` — serialize/deserialize for persistence
4. Build a simple agent that uses working memory to track UCC research state
5. After each tool call, the agent updates working memory with new findings

**Test scenario:** Multi-turn conversation researching "Greenfield Logistics LLC" — working memory tracks `current_debtor`, `findings_so_far`, and `search_history` across turns.

**Run it:**
```bash
python starter/working_memory.py
# or
node starter/working_memory.js
```

## Step 2: Episodic Memory with Vector Search

**File:** `starter/episodic_memory.py` (or `.js`)

You will:
1. Complete the `EpisodicMemory` class backed by ChromaDB
2. Implement `store_episode(conversation_summary, metadata)` — stores a conversation summary as a vector
3. Implement `recall(query, n_results=3)` — finds similar past conversations via semantic search
4. Implement `get_recent(n=5)` — returns the N most recent episodes
5. Pre-populate with 5 mock episodes from past UCC research sessions
6. Integrate episodic recall into an agent — when a user asks about a debtor, the agent first checks for similar past research

**Run it:**
```bash
python starter/episodic_memory.py
# or
node starter/episodic_memory.js
```

## Step 3: Full 3-Tier Memory Agent

**File:** `starter/memory_agent.py` (or `.js`)

You will:
1. Complete the `MemoryAgent` class that combines all three memory tiers
2. Load procedural memory from a JSON structure (learned UCC research patterns)
3. Implement the orchestration logic: check procedural patterns, recall episodes, track working state
4. Run a full research session, then run another session that recalls the first
5. Store completed research as a new episode for future recall

**Run it:**
```bash
python starter/memory_agent.py
# or
node starter/memory_agent.js
```

## Verification

After completing all three steps, run the solutions to see expected behavior:

```bash
# Python
python solution/working_memory.py
python solution/episodic_memory.py
python solution/memory_agent.py

# Node.js
node solution/working_memory.js
node solution/episodic_memory.js
node solution/memory_agent.js
```

Compare your output against `expected_output/sample_output.txt`.

## What You Built

By completing this lab, you have implemented:

1. **Working memory** — a key-value scratchpad that gives agents short-term state within a task
2. **Episodic memory** — a vector-backed store that lets agents recall similar past experiences
3. **Procedural memory** — structured patterns (JSON) that encode learned workflows and strategies
4. **Memory orchestration** — the logic that selects which memory tier to consult and when
5. **Cross-session persistence** — state that survives beyond a single conversation

This is the memory foundation for every production agent that needs to learn and improve over time.

## Next

- **M12**: Agent Evaluation and Testing
- **M13**: Human-in-the-Loop Patterns
