# M12 Lab: The ReAct Pattern & Agent Design Patterns

> **Think --> Act --> Observe --> Repeat** -- the core loop of every AI agent.

Before this lab you knew how to call tools. After it, you'll have an agent that **reasons about which tools to use and when to stop**.

## What You'll Build
A ReAct research agent with 3 UCC filing tools that reasons through multi-step questions, plus a router that classifies queries into "lookup" vs "research" and dispatches accordingly.

## Prerequisites
- Python 3.10+ or Node.js 18+
- Anthropic API key in `.env` (`ANTHROPIC_API_KEY=sk-ant-...`)
- Completed M05 (Function Calling) and M06 (Multi-Tool) labs
- Install dependencies:
  ```bash
  pip install anthropic python-dotenv
  ```

## Project Structure

```
M12-react/
├── starter/
│   ├── tools.py            # 3 research tools (complete -- don't modify)
│   ├── react_agent.py      # ReAct loop skeleton -- YOUR CODE
│   └── mock_data.py        # Mock search results (complete)
├── solution/
│   ├── tools.py
│   ├── react_agent.py      # Complete ReAct agent + router
│   └── react_agent.js      # Node.js version
└── expected_output/
    └── reasoning_trace.txt  # Full think-->act-->observe trace
```

## Lab Steps

### Step 1: Review the Tools (5 min)

The tools are complete. Read through `starter/tools.py` to understand what's available:
1. `search_filings(debtor_name, state)` -- search mock UCC data
2. `get_filing_details(filing_number)` -- full details for one filing
3. `calculate_risk(debtor_name)` -- risk score for a debtor

```bash
cd labs/M12-react/starter
python tools.py
```

Expected output:
```
M12 Tools Self-Test
search_filings('Acme'): 0 results
search_filings('Greenfield'): 2 results
get_filing_details('UCC-2024-CA-0098231'): found
calculate_risk('Greenfield Logistics'): score=0.6, level=MEDIUM
All tools working!
```

Checkpoint: You see all tool tests pass.

### Step 2: Build the ReAct Loop (25 min)

**File:** `starter/react_agent.py`

Complete the `run_react_agent()` function:
1. Send user query + tool definitions to Claude
2. Check `stop_reason` -- if `"tool_use"`, execute the tools
3. Log each Think --> Act --> Observe step
4. Loop until `stop_reason == "end_turn"` or max turns

```bash
python starter/react_agent.py
```

**Test queries:**
- `"Find all UCC filings for Greenfield Logistics"` -- single search
- `"What is the risk level for Greenfield Logistics and why?"` -- multi-step: search --> risk --> explain
- `"Get the full details of filing UCC-2024-CA-0098231"` -- direct lookup

Checkpoint: Each query shows [THINK] --> [ACT] --> [OBSERVE] --> [RESPONSE] trace in terminal.

### Step 3: Add a Query Router (15 min)

Add the `classify_query()` function and `run_with_router()`:
- "lookup" queries (direct filing number, simple search) --> single tool call
- "research" queries (risk assessment, comparisons, multi-step) --> full ReAct loop

```bash
python starter/react_agent.py --router
```

Checkpoint: Lookup queries complete in 1 turn, research queries use multiple turns.

### Step 4: Trace Logging (10 min)

Add the `format_trace()` function that outputs a clean reasoning trace:
```
Turn 1: THINK    --> "I need to search for Greenfield Logistics filings first"
Turn 1: ACT      --> search_filings(debtor_name="Greenfield Logistics")
Turn 1: OBSERVE  --> [2 filings found]
Turn 2: THINK    --> "Now I should calculate the risk score"
Turn 2: ACT      --> calculate_risk(debtor_name="Greenfield Logistics")
Turn 2: OBSERVE  --> {risk_score: 0.55, risk_level: "MEDIUM"}
Turn 3: RESPONSE --> "Greenfield Logistics has MEDIUM risk..."
```

Checkpoint: Running `python starter/react_agent.py --trace` outputs a clean numbered trace.

## Verification

```bash
python solution/react_agent.py
# or
node solution/react_agent.js
```

Compare your output to `expected_output/reasoning_trace.txt`.

## What You Built

1. **The ReAct loop** -- the Think --> Act --> Observe pattern that powers every AI agent
2. **Trace logging** -- visibility into agent reasoning (critical for debugging)
3. **A query router** -- Pattern 4 from the 8 agent design patterns
4. **Stop condition handling** -- max turns + stop_reason checking

## Next

- **M13**: Planning & Task Decomposition -- break complex tasks into DAGs
- **M14**: Multi-Agent Systems -- coordinate specialist agents
