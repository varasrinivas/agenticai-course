# M05 Lab: Function Calling Fundamentals

> **The Hero Module** — this is where a chatbot becomes an agent. The model ASKS to run tools; YOUR CODE executes them and reports back.

## Prerequisites

- M01 complete; M04 recommended (you've seen `tool_calls` once already)
- Ollama 0.3+ (`ollama --version`) — older versions don't support tools

## Exercises

| Step | File | What You Build | Key Concept |
|------|------|---------------|-------------|
| 1 | `tools.py` / `.js` | (Complete — just run) | 3 tool schemas + mock implementations + dispatcher |
| 2 | `tool_agent.py` / `.js` | The agent loop | `finish_reason`, multi-turn tool conversation |

## Step 1: Inspect the Tools

**File:** `starter/tools.py` (or `.js`) — complete. Run it standalone to sanity-check the dispatcher:

```bash
python starter/tools.py
# Defined 3 tools: get_weather, calculate, get_time
# Test: {"temp": 22, "condition": "sunny", "humidity": 45}
```

Three things to notice while reading it:
1. **Schemas use the OpenAI wrapper**: `{"type": "function", "function": {name, description, parameters}}`
2. **Descriptions are written for the model**, not for you — "Use for any math computation" is what makes Mistral pick `calculate`
3. **Tools return errors as DATA** (`{"error": "City not found..."}`), never exceptions — the model can read an error string and recover; a crash it cannot

## Step 2: The Agent Loop

**File:** `starter/tool_agent.py` (or `.js`)

Implement `agent_chat(user_message)`:

```
loop forever:
    response = client.chat.completions.create(model="mistral", tools=TOOLS, messages=messages)
    finish_reason = response.choices[0].finish_reason

    if finish_reason == "stop":        → return the text. Done.
    if finish_reason == "tool_calls":  → 1. append the assistant message
                                          (content=None, tool_calls=...) to history
                                         2. for each tool_call: run_tool(name, args),
                                            append {"role":"tool", "tool_call_id", "content"}
                                         3. loop back
    anything else                      → return an "unexpected finish_reason" message
```

The provided test harness asks four questions: weather (1 tool), math (1 tool), time (1 tool), and *"What's the capital of France?"* — which needs **no tool**; a correct loop returns the direct answer on the first pass.

**Run it:**
```bash
python starter/tool_agent.py    # or: node starter/tool_agent.js
```

## Gotchas

- **Append the assistant message BEFORE the tool results.** The API requires the `tool_calls` request and the `role: "tool"` responses to be adjacent in history, in that order, with matching `tool_call_id`s. Get this wrong and you'll see a 400 error.
- **`function.arguments` is a JSON string** — `json.loads()` it every time.
- **Add a max-turns guard** (e.g., 10 iterations) if you extend this — a confused model can loop forever asking for tools.
- **Mistral sometimes answers a tool-shaped question from memory.** Tool descriptions are your lever: the more specific, the more reliable the routing.

## Stretch Goals

- Add a 4th tool `convert_currency(amount, from, to)` with mock rates — then ask a question requiring TWO tools chained ("How many euros is the temperature in Tokyo times 10?")
- Add a `max_turns` parameter and a turn counter printout
- Log every request/response pair to a JSONL file (preview of M19 tracing)
