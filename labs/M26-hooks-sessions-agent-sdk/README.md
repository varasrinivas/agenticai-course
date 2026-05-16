# M26 Lab: Hooks, Sessions & the Agent SDK

> The Agent SDK runs the loop so you don't have to. Hooks enforce what prompts can only suggest.

In this lab you build a **UCC Filing Customer Support Agent** using the Agent SDK patterns: the agentic loop with `stop_reason`, pre/post tool use hooks, session management with fork, and subagent orchestration. Each exercise adds a layer, and the final exercise composes everything into a production-grade support agent.

## Two solution paths in this directory

| Files | What they show | When to use |
|---|---|---|
| `solution/agent_loop.py`, `hooks.py`, `session_manager.py`, ... | **Simulated SDK** — recreates the SDK's behavior with a mock client and an in-process `HookEngine`. Lets you read the lab without an API key. Useful for understanding the abstractions. | Read first to build a mental model. |
| `solution/agent_loop_sdk.py`, `hooks_sdk.py`, `session_manager_sdk.py` + `solution/.claude/agents/*.md` | **Real `claude-agent-sdk`** — the canonical M26 surface (`query()`, `@tool`, `HookMatcher`, `can_use_tool`, declarative subagents). This is what the cert exam tests and what production agents actually look like. | Run after you've read the simulation. Requires `pip install claude-agent-sdk` and an API key. |

Per `prompts/19-sdk-tier-policy.md`, M26 is **Tier 3 SDK-default** — the `*_sdk.py` files are the canonical solutions. The original simulated files remain for offline exploration only.

## Prerequisites

- Python 3.10+ or Node.js 18+
- Module M12 (ReAct Agent Loop) completed
- Module M14 (Multi-Agent Systems) completed
- Module M25 (Claude Code Mastery) completed
- No API key required (all exercises use mock responses)

## Exercises

| Step | Time | File(s) | What You Build | Key Concept |
|------|------|---------|---------------|-------------|
| 1 | 15 min | `agent_loop.py` / `.js` | Agent SDK agentic loop with stop_reason | `query()`, `stop_reason`, `maxTurns` |
| 2 | 10 min | `hooks.py` / `.js` | Pre/Post tool use hooks | Programmatic enforcement, audit logging |
| 3 | 10 min | `session_manager.py` / `.js` | Session management with fork | Named sessions, `fork_session`, stale context |
| 4 | 15 min | `subagent_coordinator.py` / `.js` | Coordinator + subagent pattern | Task tool, context isolation, parallel execution |
| 5 | 10 min | `support_agent.py` / `.js` | Full customer support agent | Composition, escalation patterns |

**Total time: ~60 minutes**

---

## Step 1: Agent SDK Agentic Loop (15 min)

**File:** `starter/agent_loop.py` (or `agent_loop.js`)

This is the core exercise. You build a simulated agent loop that mirrors the Agent SDK's `query()` behavior. The SDK runs a while loop under the hood -- you will build that loop explicitly to understand every step.

### What to implement

Open the starter file and fill in every `TODO`:

1. **The while loop body** -- Check `response.stop_reason` to decide what to do each turn.
2. **`end_turn` handling** -- Return the response when Claude considers the task complete.
3. **`tool_use` handling** -- Execute tool calls, append results to the conversation, and continue the loop.
4. **`max_tokens` handling** -- Handle the edge case gracefully.
5. **Safety net** -- Handle the case where `max_turns` is exceeded.

### Key insight

The **only** reliable way to know if the agent is done is `stop_reason`. Never parse the text output to guess. This is the single most important concept in the Agent SDK.

**Checkpoint:** Run `python starter/agent_loop.py`. You should see 3 turns (lookup filing, check risk, deliver answer) and an audit log with 3 entries.

---

## Step 2: Pre/Post Tool Use Hooks (10 min)

**File:** `starter/hooks.py` (or `hooks.js`)

Hooks provide **programmatic enforcement** -- they are guaranteed to run, unlike prompt instructions which are probabilistic (~95%).

### What to implement

1. **`refund_limit_hook`** -- A PreToolUse hook that blocks refunds over $500 (return `allowed: false`).
2. **`production_write_guard`** -- A PreToolUse hook that blocks writes to production data paths.
3. **`audit_log_hook`** -- A PostToolUse hook that logs every tool execution.
4. **`execute_with_hooks`** -- The full hook lifecycle: pre-hooks, execute, post-hooks.

### Key insight

Use **prompts** for style, tone, and non-critical guidance. Use **hooks** for spending limits, data access control, compliance rules, and audit logging. Prompts are suggestions; hooks are rules.

**Checkpoint:** Run `python starter/hooks.py`. You should see 4 scenarios: small refund (pass), large refund (blocked), filing lookup (pass), production write (blocked).

---

## Step 3: Session Management with Fork (10 min)

**File:** `starter/session_manager.py` (or `session_manager.js`)

Sessions allow an agent to persist conversation state across interactions and branch into parallel explorations.

### What to implement

1. **`create_session`** -- Create a named session with a system prompt and empty message history.
2. **`add_message`** -- Append a message and track token usage.
3. **`fork_session`** -- Create a branch from an existing session (deep copy) for parallel exploration.
4. **`is_context_stale`** -- Detect when a session's context may be outdated based on age or token usage.
5. **`compact_session`** -- Summarize old messages to reclaim context window space.

### Key insight

`fork_session` is essential for "what-if" analysis. The coordinator can fork a session, let a subagent explore a hypothesis, and discard the fork if it leads nowhere -- without polluting the main conversation.

**Checkpoint:** Run `python starter/session_manager.py`. You should see session creation, message exchange, fork, stale detection, and compaction.

---

## Step 4: Subagent Coordinator (15 min)

**File:** `starter/subagent_coordinator.py` (or `subagent_coordinator.js`)

The coordinator pattern decomposes complex tasks and delegates to specialized subagents with isolated contexts.

### What to implement

1. **`SubAgent`** -- An agent with its own system prompt, tools, and isolated message history.
2. **`Coordinator`** -- Decomposes a task into subtasks, assigns them to subagents, and aggregates results.
3. **`decompose_task`** -- Break a UCC research request into filing search, entity resolution, and risk scoring subtasks.
4. **`execute_subtask`** -- Run a subagent on its assigned subtask with context isolation.
5. **`aggregate_results`** -- Combine subagent outputs with provenance tracking.

### Key insight

Context isolation is not just an optimization -- it is a **safety feature**. Subagents should only see the information they need. The coordinator explicitly shares relevant context, never the full conversation.

**Checkpoint:** Run `python starter/subagent_coordinator.py`. You should see task decomposition, 3 parallel subagent executions, and a final aggregated report.

---

## Step 5: Full Customer Support Agent (10 min)

**File:** `starter/support_agent.py` (or `support_agent.js`)

Compose everything from Steps 1-4 into a complete customer support agent for UCC filing services.

### What to implement

1. **`SupportAgent`** -- Compose agent loop, hooks, sessions, and subagent delegation.
2. **`handle_request`** -- Route incoming requests through the full pipeline.
3. **Test scenario 1** -- Simple filing lookup (single turn, no hooks triggered).
4. **Test scenario 2** -- Refund request over $500 (blocked by hook, escalated to human).
5. **Test scenario 3** -- Cross-state entity resolution (delegated to subagents).

### Key insight

Escalation should trigger on **policy gaps** and **capability limits**, NOT on customer sentiment. An angry customer still gets automated service; a $750 refund gets escalated because it exceeds the programmatic limit.

**Checkpoint:** Run `python starter/support_agent.py`. You should see all 3 scenarios execute with hooks firing, sessions tracking, and subagents delegating as expected.

---

## Running the Labs

```bash
# Python
cd starter/
python agent_loop.py
python hooks.py
python session_manager.py
python subagent_coordinator.py
python support_agent.py

# Node.js
node agent_loop.js
node hooks.js
node session_manager.js
node subagent_coordinator.js
node support_agent.js

# Solutions (if you get stuck)
cd ../solution/
python agent_loop.py
python support_agent.py
```

## Expected Output

Compare your output against the files in `expected_output/`:
- `agent_loop_output.txt` -- Expected output from Step 1
- `support_agent_output.txt` -- Expected output from Step 5

Small differences in timestamps are fine. The structure and sequence of events should match.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `ModuleNotFoundError` | No external modules required -- all exercises use only the Python/Node.js standard library |
| Output differs from expected | Timestamps will differ. Focus on the sequence of events and tool calls |
| Node.js version errors | Ensure Node.js 18+ (uses structuredClone) |

## Key Takeaways

1. **stop_reason is the only reliable termination signal** -- never parse text to guess if the agent is done.
2. **Hooks are deterministic (100%); prompts are probabilistic (~95%)** -- use hooks for compliance-critical rules.
3. **fork_session enables safe parallel exploration** -- discard forks that lead nowhere.
4. **Context isolation is a safety feature** -- subagents see only what they need.
5. **Escalate on policy gaps, not sentiment** -- angry customers still get automated service.
