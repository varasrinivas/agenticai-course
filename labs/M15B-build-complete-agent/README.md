# M15B Lab: Build a Complete Agent & Subagent System

> This is a BUILD module. You will assemble everything from M05-M15 into one working multi-agent system.

By this point you've learned tools (M05), agentic loops (M12), planning (M13), and multi-agent coordination (M14) as separate concepts. Now you build them all into a **single, running UCC Filing Research System** — from tools to single agent to coordinator with subagents, with conversation memory on top.

**Estimated time: 2-3 hours** | **80% hands-on lab, 20% concept**

## What You'll Build

A complete UCC Filing Research System with:
- **3 tools**: `search_filings`, `get_filing_details`, `calculate_risk_score`
- **A single ReAct agent** that uses all 3 tools to research filings
- **A coordinator + 2 subagents**: filing search specialist + risk analysis specialist
- **Conversation memory**: multi-turn follow-ups with sliding window history
- **15 realistic UCC filings** across NY, CA, TX, FL, IL as mock data

## Prerequisites

- Python 3.10+ or Node.js 18+
- Anthropic API key in `.env` (`ANTHROPIC_API_KEY=sk-ant-...`)
- Completed M12 (ReAct), M14 (Multi-Agent) labs
- Install dependencies:
  ```bash
  pip install anthropic python-dotenv
  ```

## Project Structure

```
M15B-build-complete-agent/
├── starter/
│   ├── config.py          # Complete — constants, thresholds
│   ├── mock_data.py        # Complete — 15 UCC filings + search functions
│   ├── tools.py            # TODO — tool signatures, bodies are stubs
│   ├── agent.py            # TODO — single ReAct agent
│   └── coordinator.py      # TODO — coordinator + 2 subagents
├── solution/
│   ├── config.py
│   ├── mock_data.py
│   ├── tools.py            # 3 complete tools
│   ├── agent.py            # Complete single agent
│   ├── coordinator.py      # Complete coordinator + subagents
│   ├── agent.js            # Node.js single agent
│   └── coordinator.js      # Node.js coordinator
├── tests/
│   ├── test_tools.py       # Tool unit tests (no API calls)
│   ├── test_agent.py       # Agent integration tests
│   └── test_coordinator.py # Multi-agent tests
└── expected_output/
    ├── single_agent_output.txt
    └── coordinator_output.txt
```

## Lab Steps

### Step 1: Verify Mock Data (5 min)

The data is already complete. Run it to see what you're working with:

```bash
cd starter
python mock_data.py
```

You should see: 15 filings, 5 states, 5 unique debtors (Acme appears in all 5 states).

### Step 2: Build the Tools (30 min)

**File:** `starter/tools.py`

Build 3 tool functions and their JSON Schema definitions:
1. `search_filings(debtor_name, state)` — search mock data, return matching filings
2. `get_filing_details(filing_number)` — return full details for one filing
3. `calculate_risk_score(debtor_name)` — analyze all filings for a debtor, return risk profile

**Run tests:**
```bash
python -m pytest ../tests/test_tools.py -v
```

**Checkpoint:** All tool tests pass. Each tool returns structured JSON.

### Step 3: Build the Single Agent (30 min)

**File:** `starter/agent.py`

Build a ReAct agent that uses all 3 tools:
1. System prompt with agent role and tool descriptions
2. ReAct loop: send → check stop_reason → execute tools → loop
3. Trace logging for every Think → Act → Observe step

**Test scenarios:**
```bash
python starter/agent.py
```
- `"Find all UCC filings for Acme Corporation in New York"` → finds 2 filings
- `"What's the risk level for Acme Corporation?"` → HIGH risk (multiple states, blanket liens)
- `"What about their filings in Texas?"` → finds 1 Texas filing

**Checkpoint:** All 3 queries produce correct, sourced responses.

### Step 4: Build the Coordinator + Subagents (45 min)

**File:** `starter/coordinator.py`

Upgrade from single agent to coordinator + 2 specialist subagents:

1. **Filing Search Subagent** — own system prompt, tools: `search_filings`, `get_filing_details`
   - Task: "Search for UCC filings for {debtor_name} in {states}"
   - Returns: `{filings: [...], count: N, states_searched: [...]}`

2. **Risk Analysis Subagent** — own system prompt, tools: `calculate_risk_score`, `search_filings`
   - Task: "Calculate lien risk for {debtor_name}"
   - Returns: `{risk_score: 0.73, risk_level: "HIGH", factors: [...], recommendation: "..."}`

3. **Coordinator** — receives user questions, decides which subagent(s) to call, passes EXPLICIT context, synthesizes results

**Test scenarios:**
```bash
python starter/coordinator.py
```
- Same queries as Step 3, now routed through coordinator
- Error case: `"Find filings for NonExistent Corp"` → handled gracefully

**Checkpoint:** Same quality answers, cleaner architecture, visible handoffs.

### Step 5: Add Conversation Memory (20 min)

Add sliding-window history to the coordinator:
- Track last 5 user questions and agent responses
- Handle follow-ups: `"What about Texas?"` understands previous context
- History is passed in the coordinator's system prompt

**Test multi-turn:**
```bash
# In coordinator.py, the main block runs a multi-turn session
python starter/coordinator.py
```

### Step 6: Run the Full Test Suite

```bash
python -m pytest tests/ -v
```

## Verification

Run the solutions to see expected behavior:

```bash
# Single agent
python solution/agent.py

# Coordinator with subagents
python solution/coordinator.py

# Node.js versions
node solution/agent.js
node solution/coordinator.js
```

## What You Built

1. **3 production-style tools** with JSON Schema, error handling, and structured responses
2. **A single ReAct agent** implementing the full reason → act → observe loop
3. **A coordinator + 2 subagents** with explicit context passing and isolated conversations
4. **Conversation memory** for multi-turn follow-up handling
5. **A complete, running multi-agent system** on your laptop

## Architecture Reflection

What you built works, but it's not production-ready yet. The next modules add:
- **M16-M17**: Input/output guardrails (prevent prompt injection, validate responses)
- **M19-M20**: Observability (trace every decision, measure latency and cost)
- **M21-M22**: Deployment (containerize, deploy to cloud, handle scale)

You now have a working multi-agent system. The next modules add the production layers.

## Next

- **M16**: Input Guardrails — protect your agent from malicious inputs
- **M17**: Output Guardrails & Human-in-the-Loop
