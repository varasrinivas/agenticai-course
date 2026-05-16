# M15B — SDK Solution (Tier 3 reference)

This is the **canonical SDK-based solution** for M15B. It builds the same UCC filing research system as `solution/`, but uses `claude-agent-sdk` and declarative subagents instead of a hand-rolled `while` loop.

## How this differs from `solution/`

| | `solution/` (manual) | `solution-sdk/` (this directory) |
|---|---|---|
| Loop | hand-written `while stop_reason == "tool_use"` | `async for msg in query(...)` |
| Tools | JSON Schema dicts in `TOOL_DEFINITIONS` | `@tool`-decorated async fns + `create_sdk_mcp_server` |
| Subagents | Python classes + a manual coordinator that calls each | `.claude/agents/*.md` files; SDK manages dispatch + isolated context |
| Hooks | None — inline logging in the loop | `HookMatcher` for `PreToolUse`/`PostToolUse` |
| Permission gate | None | `can_use_tool` callback returning `Allow`/`Deny` |
| Sessions | `messages.append(...)` | `SessionManager` re-passes transcript to `query()` |
| Lines of code | ~300 (agent.py + coordinator.py + tools.py) | ~150 + 2 markdown subagents |

## Run

```powershell
pip install -r requirements.txt
$env:ANTHROPIC_API_KEY = "sk-..."
python coordinator.py "What is the lien exposure for Acme Corporation?"
python session_manager.py    # multi-turn + fork demo
```

## The spec-driven path

The same agent can be regenerated from `../spec/agent-spec.md` with:

```
claude
> /generate-from-spec ../spec/agent-spec.md
```

This is the workflow Section 5B of M15B walks through. The output goes to `../generated/` — diff it against this directory to see how close spec-driven gets to a hand-tuned reference.
