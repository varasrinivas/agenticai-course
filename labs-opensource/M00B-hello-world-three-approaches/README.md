# M00B Lab: Hello World, Three Approaches

> Build the SAME agent three times — a world-clock assistant with one `get_time` tool — using three abstraction levels: raw OpenAI SDK, CrewAI, and LangChain. Feeling the difference is the whole point.

## Prerequisites

- M00 complete (Ollama serving `mistral`)
- Dependencies:
  ```bash
  # Python
  pip install openai "crewai[tools]" langchain langchain-community langchain-core

  # Node.js (raw + LangChain only — CrewAI is Python-only)
  npm install openai langchain @langchain/ollama @langchain/core zod
  ```

## Exercises

| Step | File | Abstraction Level | What You Build |
|------|------|------------------|----------------|
| 1 | `raw_agent.py` / `.js` | None — you write the loop | Hand-rolled tool-use loop |
| 2 | `crewai_agent.py` (Python only) | High — declarative roles | Agent/Task/Crew config |
| 3 | `langchain_agent.py` / `.js` | Medium — composable chains | Prompt → LLM → AgentExecutor |

The `get_time` tool implementation and the `TIMEZONES` map are **provided in every starter** — you build the agent wiring around them.

## Step 1: Raw OpenAI SDK Loop

**File:** `starter/raw_agent.py` (or `.js`)

You will implement `run_agent()`:
1. Start a `messages` list with the user's question
2. Loop: call `client.chat.completions.create()` with `tools=TOOLS` and `tool_choice="auto"`
3. If `message.tool_calls` is empty/None → the model is done, return `message.content`
4. Otherwise: append the assistant message, then for each tool call, parse `tc.function.arguments` (a JSON **string**), execute `get_time`, and append a `{"role": "tool", "tool_call_id": tc.id, "content": result}` message
5. Loop back to step 2

```bash
python starter/raw_agent.py     # or: node starter/raw_agent.js
```

**Test:** "What time is it in Tokyo right now?" should trigger one tool call, then a natural-language answer containing the actual time.

## Step 2: CrewAI (Python only)

**File:** `starter/crewai_agent.py`

You will:
1. Decorate the provided `get_time` function with `@tool("Get City Time")` (the docstring becomes the tool description)
2. Define an `Agent` with `role`, `goal`, `backstory`, `tools=[get_time]`, and `llm="ollama/mistral"` (LiteLLM `provider/model` format)
3. Define a `Task` with `description` and `expected_output`
4. Create a `Crew` and call `kickoff()`

Notice what you did NOT write: no loop, no JSON parsing, no message bookkeeping. CrewAI does it.

> CrewAI has no official JavaScript package. The Node.js equivalent is a thin declarative wrapper over the raw loop — see `solution/crewai_style_agent.js` for the pattern.

## Step 3: LangChain

**File:** `starter/langchain_agent.py` (or `.js`)

You will:
1. Decorate `get_time` with LangChain's `@tool` (Python) or wrap it with `tool(fn, {name, description, schema})` (JS, Zod schema)
2. Create `ChatOllama(model="mistral")` as the LLM
3. Build a `ChatPromptTemplate` with system + human messages and a `MessagesPlaceholder("agent_scratchpad")` — LangChain injects the tool-call history there
4. Wire it together: `create_openai_tools_agent(llm, tools, prompt)` → `AgentExecutor` → `invoke()`

```bash
python starter/langchain_agent.py     # or: node starter/langchain_agent.js
```

## What to Compare When You're Done

Run all three and ask yourself:
- **Lines of code you wrote**: raw ≈ 30, CrewAI ≈ 15, LangChain ≈ 20
- **Debuggability**: in which version can you print every message that hits the model?
- **Control**: which version lets you change the loop's exit condition?

Rule of thumb from the module: raw SDK when you need control and learning, CrewAI for quick multi-agent role play, LangChain when you want its ecosystem (retrievers, memory, integrations).

## Gotchas

- **Framework versions move fast.** If CrewAI or LangChain imports fail, check the solution file headers for the API used and consult the framework changelog. The raw SDK version (Step 1) is the stable reference.
- **`tc.function.arguments` is a JSON string, not a dict** — always `json.loads()` / `JSON.parse()` it.
- **Mistral occasionally answers without calling the tool.** Re-run, or strengthen the system prompt ("Always use the get_time tool for time questions").
