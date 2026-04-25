# M14 Lab: Multi-Agent Systems

> One agent does everything. A team of specialist agents does it better.

When an agent has too many tools (5+) or tasks that require different expertise, tool selection accuracy degrades and context grows unwieldy. The solution: split into specialist agents coordinated by a supervisor. In this lab you build a 4-agent content pipeline — researcher, analyst, writer, and reviewer — orchestrated by a coordinator.

## Prerequisites

- Python 3.10+ or Node.js 18+
- Anthropic API key in `.env` file (`ANTHROPIC_API_KEY=sk-ant-...`)
- Completed M12 (ReAct) and M13 (Planning) labs
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
| 1 | `multi_agent.py` / `multi_agent.js` | 4-agent pipeline with coordinator: researcher → analyst → writer → reviewer | Supervisor/worker pattern, explicit context passing, subagent isolation |

## Step 1: Build a Multi-Agent Content Pipeline

**File:** `starter/multi_agent.py` (or `.js`)

You will:
1. Implement `run_subagent()` — runs a specialist agent with its own system prompt, tools, and isolated context
2. Build 4 specialist agent functions:
   - `run_researcher(task)` — searches for UCC filings using `search_filings` and `get_filing_details`
   - `run_analyst(task, research_data)` — analyzes filings using `calculate_risk`, identifies patterns
   - `run_writer(task, analysis)` — generates a report section from analysis findings
   - `run_reviewer(task, report)` — reviews the report for accuracy and completeness
3. Build the coordinator: `run_coordinator(user_query)` — delegates to specialists in sequence, passing results explicitly
4. Test with:
   - `"Create a risk analysis report for Greenfield Logistics LLC"`
   - `"Research and compare Nextera Holdings and Peachtree Ventures"`

**Critical concept:** Each subagent gets its OWN system prompt and context. The coordinator passes results EXPLICITLY — subagents do NOT inherit the coordinator's conversation history.

**Run it:**
```bash
python starter/multi_agent.py
# or
node starter/multi_agent.js
```

**Checkpoint:** You see 4 separate agent invocations per query. Each agent receives only the context it needs. The final output is a reviewed report.

## Verification

```bash
# Python
python solution/multi_agent.py

# Node.js
node solution/multi_agent.js
```

Compare your output against `expected_output/sample_output.txt`.

## What You Built

1. **Supervisor/worker pattern** — a coordinator that delegates to specialist agents
2. **Context isolation** — each subagent has its own system prompt and conversation, not the coordinator's
3. **Explicit handoff** — results are passed between agents as structured data, not inherited
4. **Pipeline execution** — agents run in sequence: research → analyze → write → review
5. **Error handling** — coordinator handles subagent failures gracefully

## Next

- **M15**: Code Interpreter & Sandbox — let agents write and execute code
- **M15B**: Build a Complete Agent System — assemble everything from M05-M15 into one working system
