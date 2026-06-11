# M06 Lab: Multi-Tool Orchestration

> One tool makes a helper; five tools make an orchestra. You'll build a research assistant that runs independent searches in PARALLEL, chains dependent calls SEQUENTIALLY, recovers from tool errors, and filters its toolbox by phase.

## Prerequisites

- M05 complete (you've built a single agent loop)

## Exercises

| Step | File | What You Build | Key Concept |
|------|------|---------------|-------------|
| 1 | `tools_registry.py` / `.js` | (Complete — just run) | 5 tool schemas, mocks with a deliberate 404, `execute_tool`, `ToolRegistry` |
| 2 | `research_agent.py` / `.js` | The orchestrating loop | Parallel vs sequential execution, error recovery, tag filtering |

## Step 1: Inspect the Toolbox

**File:** `starter/tools_registry.py` (or `.js`) — complete. Run it standalone:

```bash
python starter/tools_registry.py
```

Things to notice:
- **Descriptions choreograph the chain**: `fetch_page` says "Use after web_search", `summarize_text` says "Use after fetch_page" — that's how the model learns the sequence without hardcoded logic
- **`web_search` deliberately returns one broken URL** (`broken.example.com/404`) and `fetch_page` raises on it — your loop must survive this
- **`execute_tool` returns `(result_json, is_error)`** — errors become data the model can read
- **`ToolRegistry`** filters tools by tag (`research`, `citation`, `output`) so different phases see different toolboxes

## Step 2: The Orchestrating Loop

**File:** `starter/research_agent.py` (or `.js`)

Implement `run_agent(question, tool_tags)`. It's the M05 loop plus three upgrades:

1. **Tool filtering**: `active_tools = registry.get_tools_for_context(tags=tool_tags)`
2. **Max iterations guard**: `for iteration in range(10)` instead of `while True`
3. **Parallel execution**: when the model requests >1 tool call in a single response, execute them concurrently — `ThreadPoolExecutor` + `as_completed` in Python, `Promise.all` in Node — and append ALL results before looping back

The provided test harness runs four scenarios: parallel search (3 topics at once), a sequential chain (search → fetch → summarize), error recovery (the 404 URL), and tag filtering (citation tools only).

```bash
python starter/research_agent.py    # or: node starter/research_agent.js
```

## Gotchas

- **Every `tool_call_id` needs a matching `role: "tool"` result** — even (especially!) the failed ones. Skip one and the API rejects your next request.
- **Order of results doesn't matter, IDs do.** `as_completed` returns futures in finish order, not request order — that's fine because matching happens by `tool_call_id`.
- **Mistral-7B parallelizes less eagerly than larger models.** If Test 1 runs sequentially, that's a model choice, not a bug in your loop — the system prompt nudges it, but doesn't guarantee it.

## Stretch Goals

- Add a **circuit breaker**: after 2 consecutive failures of the same tool, unregister it and tell the model it's unavailable
- Time the parallel vs sequential paths (the mocks sleep 200–300ms, so 3 parallel searches should take ~0.3s, not ~0.9s)
