# M13 Lab: Planning & Task Decomposition

> Complex tasks need a plan. Your agent should think before it acts.

A ReAct agent (M12) can reason step by step, but it decides what to do next on the fly. For complex multi-step tasks — like generating a full risk report — the agent should first **decompose** the task into a plan, then execute each step. In this lab you build a planning agent that breaks "Generate a complete risk report for Acme Corporation" into a DAG of sub-tasks and executes them in order.

## Prerequisites

- Python 3.10+ or Node.js 18+
- Anthropic API key in `.env` file (`ANTHROPIC_API_KEY=sk-ant-...`)
- Completed M12 lab (ReAct pattern)
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
| 1 | `planning_agent.py` / `planning_agent.js` | Planning agent that decomposes tasks into a DAG and executes step by step | Task decomposition, DAG execution, plan-then-act pattern |

## Step 1: Build a Planning Agent

**File:** `starter/planning_agent.py` (or `.js`)

You will:
1. Implement `create_plan()` — asks Claude to decompose a complex query into ordered sub-tasks with dependencies
2. Implement `execute_step()` — runs a single sub-task using the ReAct pattern from M12
3. Implement `run_plan()` — executes the full plan respecting task dependencies (sequential DAG)
4. Wire up 4 tools: `search_filings`, `get_filing_details`, `calculate_risk`, `generate_report_section`
5. Test with two scenarios:
   - `"Generate a complete risk report for Greenfield Logistics LLC"`
   - `"Compare lien exposure between Nextera Holdings and Lone Star Energy"`

**Run it:**
```bash
python starter/planning_agent.py
# or
node starter/planning_agent.js
```

**Checkpoint:** The agent produces a plan with 3-5 steps before executing anything. Each step runs in order, and the final output combines all step results into a coherent report.

## Verification

```bash
# Python
python solution/planning_agent.py

# Node.js
node solution/planning_agent.js
```

Compare your output against `expected_output/sample_output.txt`.

## What You Built

1. **Task decomposition** — teaching an agent to break complex requests into manageable sub-tasks before acting
2. **Plan-then-act pattern** — separating planning from execution for better reliability
3. **DAG execution** — running sub-tasks in dependency order, passing results from earlier steps to later ones
4. **Report generation** — synthesizing multi-step results into a coherent final output

## Next

- **M14**: Multi-Agent Systems — instead of one agent doing everything, split into specialist agents
- **M15**: Code Interpreter — let agents write and run code for computation
