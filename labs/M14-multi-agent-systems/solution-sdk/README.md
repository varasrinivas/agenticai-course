# M14 — SDK Solution (declarative subagents)

This is the **dual-track companion** to `solution/multi_agent.py`. Same four-stage pipeline (researcher → analyst → writer → reviewer) but the workers are declared as `.claude/agents/<name>.md` files, and the coordinator is a single `query()` call.

## Side-by-side

| | `solution/multi_agent.py` | `solution-sdk/` (this dir) |
|---|---|---|
| Workers | Python classes/functions, each with its own `client.messages.create()` loop | Markdown files in `.claude/agents/` with frontmatter (name, description, tools, model) |
| Coordinator | ~250 lines: builds messages, dispatches workers, aggregates results | ~80 lines: one `query()` call with a coordinator system prompt that names the subagents |
| Context isolation | Manually constructed dicts passed between workers | SDK gives each subagent a fresh context window when invoked by name |
| Model selection per worker | Hardcoded in each worker's `client.messages.create()` | Set in each subagent's frontmatter `model:` field |

## Run

```powershell
pip install claude-agent-sdk
$env:ANTHROPIC_API_KEY = "sk-..."
python coordinator.py "Acme Corporation"
```

The coordinator delegates to each subagent in turn. The subagents are invoked by name — Claude Code reads the `.claude/agents/` directory automatically.

## What to compare

Run both versions on the same input. They should produce equivalent reports. The SDK version is shorter and the worker definitions are reviewable in isolation (each one is a single Markdown file).
