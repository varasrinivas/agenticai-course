# M12 Lab: The ReAct Agent Loop

> A chatbot answers. An agent **reasons, acts, and observes** in a loop until the job is done.

In this lab you build a ReAct (Reason + Act) agent that uses Claude's tool-use API to research UCC filings. The agent thinks about what to do, calls a tool, observes the result, and decides whether to continue or stop. You will see the full thought → action → observation trace logged to the console.

## Prerequisites

- Python 3.10+ or Node.js 18+
- Anthropic API key in `.env` file (`ANTHROPIC_API_KEY=sk-ant-...`)
- Install dependencies:
  ```bash
  # Python
  pip install anthropic python-dotenv

  # Node.js
  npm install @anthropic-ai/sdk dotenv
  ```

## Exercises

| Step | File | What You Build | Key Concept |
|------|------|---------------|-------------|
| 1 | `react_agent.py` / `react_agent.js` | ReAct research agent with 3 tools, full trace logging, stop-condition handling | Agent loop, stop_reason, thought traces, max iterations |

## Step 1: Build a ReAct Research Agent

**File:** `starter/react_agent.py` (or `.js`)

You will:
1. Define 3 tools: `search_filings`, `get_filing_details`, `calculate_risk` — each with a JSON Schema
2. Implement `execute_tool()` — dispatches tool calls to the mock data layer
3. Build the ReAct loop:
   - Send messages to Claude with tool definitions
   - Check `stop_reason`: if `"tool_use"` → execute tools and loop; if `"end_turn"` → done
   - Log every Think → Act → Observe step with the `observe_*` helpers
   - Enforce a `max_turns` safety cap (default 10)
4. Run 3 test queries:
   - `"Find all UCC filings for Greenfield Logistics in New York"`
   - `"What's the risk profile for Nextera Holdings Corp?"`
   - `"Search for filings in Texas and tell me about the collateral"`

**Run it:**
```bash
python starter/react_agent.py
# or
node starter/react_agent.js
```

**Checkpoint:** Each query produces a sourced answer. The console shows at least 2 tool calls per query. No infinite loops.

## Verification

After completing the exercise, run the solution to see expected behavior:

```bash
# Python
python solution/react_agent.py

# Node.js
node solution/react_agent.js
```

Compare your output against `expected_output/sample_output.txt`.

## What You Built

By completing this lab, you have implemented:

1. **The ReAct loop** — the core pattern behind every Claude agent: reason → act → observe → repeat
2. **Tool dispatch** — routing Claude's tool_use requests to your functions and returning structured results
3. **Stop-condition handling** — checking `stop_reason` to know when Claude wants a tool vs. when it's done
4. **Trace logging** — visibility into every step the agent takes (essential for debugging and observability)
5. **Safety caps** — `max_turns` to prevent runaway loops

This is the foundation pattern for every agent you'll build in M13–M15B.

## Next

- **M13**: Planning & Task Decomposition — teach your agent to break complex tasks into sub-tasks before acting
- **M14**: Multi-Agent Systems — split one big agent into a team of specialists
