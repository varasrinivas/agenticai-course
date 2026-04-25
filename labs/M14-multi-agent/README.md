# M14 Lab: Multi-Agent Systems

> **One agent, many tools -> many agents, each a specialist.** When a single agent gets overloaded, split into a team.

## What You'll Build
A 4-agent content pipeline that researches UCC filings, analyzes patterns, writes a risk report, and reviews it for accuracy — all orchestrated by a coordinator.

## Prerequisites
- Python 3.10+ or Node.js 18+
- Anthropic API key in `.env`
- Completed M12 (ReAct) and M13 (Planning) labs
- Install: `pip install anthropic python-dotenv`

## Project Structure
```
M14-multi-agent/
├── starter/
│   ├── coordinator.py      # Coordinator skeleton — YOUR CODE
│   ├── researcher.py       # Researcher subagent skeleton
│   ├── analyst.py          # Analyst subagent skeleton
│   ├── writer.py           # Writer subagent skeleton
│   ├── reviewer.py         # Reviewer subagent skeleton (BONUS)
│   ├── tools.py            # Research tools (complete)
│   └── mock_data.py        # Wraps shared mock data (complete)
├── solution/
│   ├── coordinator.py      # Complete coordinator
│   ├── researcher.py       # Complete researcher
│   ├── analyst.py          # Complete analyst
│   ├── writer.py           # Complete writer
│   ├── reviewer.py         # Complete reviewer
│   └── coordinator.js      # Node.js version (all-in-one)
└── expected_output/
    └── pipeline_output.txt # Full pipeline trace
```

## Lab Steps

### Step 1: Build the Researcher (20 min)
**File:** `starter/researcher.py`
- Has tools: search_filings, get_filing_details
- Task: "Find all UCC filings for {entity}" across all states
- Returns structured findings: list of filings with key details

### Step 2: Build the Analyst (15 min)
**File:** `starter/analyst.py`
- Has tool: calculate_risk
- Takes researcher's findings as input
- Identifies patterns: multi-state exposure, blanket liens, secured party concentration
- Returns analysis summary

### Step 3: Build the Writer (15 min)
**File:** `starter/writer.py`
- No tools — purely text generation
- Takes researcher findings + analyst analysis
- Produces a formatted risk report (Executive Summary, Details, Assessment, Recommendation)

### Step 4: Build the Reviewer (BONUS — 10 min)
**File:** `starter/reviewer.py`
- No tools — quality check
- Verifies: all filing numbers cited exist in the researcher's data, risk level matches analyst's calculation, no fabricated information
- Returns: APPROVED or NEEDS REVISION with feedback

### Step 5: Build the Coordinator (20 min)
**File:** `starter/coordinator.py`
- Orchestrates: Researcher -> Analyst -> Writer -> Reviewer
- Passes context EXPLICITLY between agents (not shared memory)
- Handles failures: if researcher finds nothing, skip analyst/writer
- Logs all handoffs with data size

### Step 6: Run the Pipeline
```bash
python starter/coordinator.py "Acme Corporation"
```

Checkpoint: See [COORDINATOR] -> [RESEARCHER] -> [ANALYST] -> [WRITER] -> [REVIEWER] -> [FINAL REPORT]

## Verification
```bash
python solution/coordinator.py "Acme Corporation"
node solution/coordinator.js
```

## What You Built
1. **Specialist agents** with isolated context and focused tools
2. **Pipeline coordination** — sequential handoffs with explicit context
3. **Agent communication** — structured data passing between agents
4. **Quality review** — reviewer agent that validates output

## Next
- **M15**: Code Interpreter & Sandbox Execution
- **M15B**: Build a Complete Agent & Subagent System (the big BUILD module)
