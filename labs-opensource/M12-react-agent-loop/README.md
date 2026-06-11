# M12 Lab: The ReAct Agent Loop

> Reason → Act → Observe → Repeat. The system prompt forces Mistral to write a `Thought:` before every tool call — visible reasoning improves tool selection 10-40% on knowledge-intensive tasks (Yao et al. 2022) and gives you a debuggable trace for free.

## Prerequisites

- M05/M06 complete (you can write a tool loop in your sleep by now)

## Exercises

| Step | File | What You Build | Key Concept |
|------|------|---------------|-------------|
| 1 | `mock_search.py` / `.js` | (Complete) Deterministic mock web search | Develop against mocks, swap real APIs later |
| 2 | `react_agent.py` / `.js` | The ReAct loop with thought traces | Reason/Act/Observe phases, stop conditions |

## What Makes This Loop "ReAct" (vs M05's plain loop)

Mechanically it's the same `finish_reason` loop. Three additions:

1. **The system prompt demands thoughts**: *"Before EVERY tool call, write `Thought: [reasoning]`. After EVERY tool result, write `Thought: [what you learned]`."* The thought arrives as `message.content` ALONGSIDE `tool_calls` in the same response — print it.
2. **A structured final deliverable**: Summary / Key Findings / Sources Used — so "done" is observable.
3. **An explicit safety cap** (`max_turns=20`) with the loop normally exiting via `finish_reason == "stop"`, never the cap.

## Step 2: `run_agent(question, max_turns=20, verbose=True)`

```
while turn < max_turns:
    turn += 1
    response = client.chat.completions.create(model="mistral",
        messages=[system] + messages, tools=TOOLS)
    msg = response.choices[0].message

    if verbose: print the Thought (msg.content) and any tool calls   ← the ReAct part
    if finish_reason == "stop": return msg.content                   ← natural exit
    append assistant msg (content + tool_calls), then for each call:
        result = execute_tool(...); append role:"tool" message       ← Observe
return "[Safety cap reached]"                                         ← abnormal exit
```

**Key detail the plain M05 loop didn't have:** keep `msg.content` when appending the assistant message — the thought text is part of the conversation history and helps the model stay coherent on the next iteration.

## Run It

```bash
python starter/react_agent.py
```

The test question — *"What are the main Python frameworks for building AI agents in 2025, and how does the claude-agent-sdk compare?"* — needs 2-3 searches. Watch the printed trace: Thought → search → Thought → search → final report.

## Troubleshooting (from the course)

- **No `Thought:` lines?** Mistral-7B sometimes skips them. Strengthen the instruction ("You MUST write Thought: before each tool call") or lower temperature.
- **Loop never ends?** Check you return on `finish_reason == "stop"` — and that the system prompt defines what a finished report looks like.
- **Same search repeated?** The model can't see past results if you forgot to append the `role: "tool"` messages.

## Stretch Goals

- Add a second tool (`get_date`) and watch the reasoning choose between tools
- Count thought-words per turn; correlate trace verbosity with answer quality
- Swap `mock_search` for a real search API via `httpx` (keep the mock for tests!)
