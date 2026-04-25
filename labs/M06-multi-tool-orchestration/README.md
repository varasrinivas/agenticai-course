# M06 Lab: Multi-Tool Orchestration

> **From one tool to five** -- your agent learns to juggle parallel calls,
> chain outputs between tools, and pick the right tool for every job.

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
| 1 | `parallel_tools.py` / `parallel_tools.js` | Parallel tool dispatch -- agent handles multiple tool calls in one response | Parallel tool_use blocks, Promise.all vs sequential |
| 2 | `tool_chain.py` / `tool_chain.js` | Sequential tool chain -- output of one tool feeds into the next | Tool chaining, data pipelines between tools |
| 3 | `research_assistant.py` / `research_assistant.js` | Full research assistant with 5 tools for UCC filing research | Tool selection with many tools, routing strategies |

## Step 1: Parallel Tool Dispatch

**File:** `starter/parallel_tools.py` (or `.js`)

You will:
1. Use 3 pre-defined tools: `get_weather`, `calculate`, `get_time` (same as M05)
2. Implement the agent loop that **explicitly handles MULTIPLE tool_use blocks** in a single response
3. Process all parallel tool calls and send ALL results back in one message
4. Compare parallel vs sequential execution timing

**Key difference from M05:** In M05, the multi-tool handling was part of the overall agent loop. Here, you focus specifically on the parallel dispatch pattern -- timing each call, processing them concurrently (JS: `Promise.all`), and understanding when Claude chooses parallel vs sequential.

**Test queries:**
- `"What's the weather in Tokyo, New York, and London?"` -- Claude should call get_weather 3 times in parallel
- `"What's the weather in Paris and what time is it in EST?"` -- parallel across different tools
- `"What is 25 * 4 and what is 100 / 3?"` -- parallel calculate calls

**Run it:**
```bash
python starter/parallel_tools.py
# or
node starter/parallel_tools.js
```

## Step 2: Sequential Tool Chain

**File:** `starter/tool_chain.py` (or `.js`)

You will:
1. Use 3 tools: `search_filings`, `get_filing_details`, `summarize_text` -- with inline mock data
2. Implement the agent loop that supports **multi-turn tool chaining**
3. Claude calls tool 1 (search) -> gets results -> calls tool 2 (details) -> gets results -> calls tool 3 (summarize)
4. Each tool's output naturally feeds into Claude's decision to call the next tool

**Key concept:** Claude drives the chain. You don't hardcode the order -- Claude sees the results from tool 1 and decides to call tool 2. Your job is to implement the loop that supports this multi-turn conversation.

**Test queries:**
- `"Find filings for Greenfield Logistics and summarize the collateral"` -- triggers the full 3-step chain
- `"Get details on filing UCC-2024-001 and summarize it"` -- 2-step chain
- `"Search for filings in New York"` -- single tool, no chain

**Run it:**
```bash
python starter/tool_chain.py
# or
node starter/tool_chain.js
```

## Step 3: Full Research Assistant (5 Tools)

**File:** `starter/research_assistant.py` (or `.js`)

You will:
1. Use 5 tools with shared UCC mock data: `search_filings`, `get_filing_details`, `summarize_text`, `calculate_risk_score`, `generate_report`
2. Implement the agent loop with a **tool dispatcher** that routes to the correct function
3. Handle complex queries where Claude selects 2-4 tools across multiple turns
4. Test with realistic UCC research scenarios

**Tools:**
| Tool | Purpose |
|------|---------|
| `search_filings` | Search UCC filings by debtor name, state, status |
| `get_filing_details` | Get full details for a specific filing number |
| `summarize_text` | Summarize a collateral description into plain English |
| `calculate_risk_score` | Calculate lien risk score from filing count + collateral types |
| `generate_report` | Generate a formatted report from gathered data |

**Test queries:**
- `"Find all active filings in New York and summarize their collateral"` -- search + summarize chain
- `"What's the risk score for Greenfield Logistics LLC?"` -- search + calculate chain
- `"Generate a report on all filings in Texas"` -- search + details + report chain

**Run it:**
```bash
python starter/research_assistant.py
# or
node starter/research_assistant.js
```

## Verification

After completing all three steps, run the solutions to see expected behavior:

```bash
# Python
python solution/parallel_tools.py
python solution/tool_chain.py
python solution/research_assistant.py

# Node.js
node solution/parallel_tools.js
node solution/tool_chain.js
node solution/research_assistant.js
```

Compare your output against `expected_output/sample_output.txt`.

## What You Built

By completing this lab, you have implemented:

1. **Parallel tool dispatch** -- processing multiple tool_use blocks concurrently and sending all results back at once
2. **Sequential tool chains** -- multi-turn loops where one tool's output feeds into the next tool's input
3. **Multi-tool routing** -- a dispatcher that maps 5 different tools to their implementations
4. **Tool selection at scale** -- letting Claude choose from many tools based on the query
5. **UCC research patterns** -- domain-specific tool orchestration for public records analysis

This is the bridge from "agent with tools" to "agent that orchestrates workflows."

## Next

- **M07**: Multi-Turn Conversation Management
- **M08**: Memory and Context Window Strategies
