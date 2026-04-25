# M13 Lab: Planning & Task Decomposition

> **"How do you eat an elephant? One bite at a time."** — Complex tasks need a plan.

## What You'll Build
A planning agent that takes a complex research request, decomposes it into a DAG of sub-tasks, and executes them in dependency order — producing a complete UCC risk report.

## Prerequisites
- Python 3.10+ or Node.js 18+
- Anthropic API key in `.env`
- Completed M12 (ReAct) lab
- Install: `pip install anthropic python-dotenv`

## Project Structure
```
M13-planning/
├── starter/
│   ├── tools.py            # Research tools (complete)
│   ├── planner.py          # Planning agent skeleton — YOUR CODE
│   └── mock_data.py        # Wraps shared mock data (complete)
├── solution/
│   ├── tools.py
│   ├── planner.py          # Complete planning agent
│   └── planner.js          # Node.js version
└── expected_output/
    └── plan_execution.txt  # Full plan → execute trace
```

## Lab Steps

### Step 1: Review the Tools (5 min)
Same tools from M12: search_filings, get_filing_details, calculate_risk.

### Step 2: Build the Task Planner (20 min)
**File:** `starter/planner.py`

Implement `create_plan(goal)`:
- Ask Claude to decompose the goal into ordered sub-tasks
- Return a list of {id, task, tool, depends_on, status} dicts
- Each task specifies which tool to use

### Step 3: Build the Plan Executor (25 min)
Implement `execute_plan(plan)`:
- Walk the DAG: only execute a task when its dependencies are done
- Execute each task using the ReAct pattern from M12
- Collect results, pass them as context to dependent tasks
- Handle failures: mark task as FAILED, skip dependents

### Step 4: Generate the Risk Report (15 min)
Implement `synthesize_report(goal, results)`:
- Take all completed task results
- Ask Claude to synthesize into a structured report with:
  - Executive Summary, Filing Details, Risk Assessment, Recommendation

### Step 5: Run End-to-End
```bash
python starter/planner.py "Generate a complete risk report for Acme Corporation"
```

Checkpoint: See plan creation, task execution, and report synthesis in sequence.

## Verification
```bash
python solution/planner.py "Generate a complete risk report for Acme Corporation"
node solution/planner.js
```

## What You Built
1. **Task decomposition** — breaking complex goals into executable sub-tasks
2. **DAG execution** — respecting dependencies between tasks
3. **Result aggregation** — synthesizing sub-task outputs into a report
4. **Failure handling** — graceful degradation when tasks fail

## Next
- **M14**: Multi-Agent Systems — delegate sub-tasks to specialist agents
