# M15 Lab: Code Interpreter & Sandbox Execution

> LLMs can reason about math but can't reliably compute it. Let your agent write and run code instead.

Claude is great at reasoning, but when it needs to count filings per state, calculate averages, or generate charts, it should write Python code and execute it. In this lab you build a code execution tool that runs agent-generated Python in a sandboxed subprocess, then wire it into a ReAct agent that analyzes UCC filing data through code.

## Prerequisites

- Python 3.10+ or Node.js 18+
- Anthropic API key in `.env` file (`ANTHROPIC_API_KEY=sk-ant-...`)
- Completed M12 (ReAct) lab
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
| 1 | `code_interpreter.py` / `code_interpreter.js` | Agent that writes & executes Python to analyze UCC data — with sandboxed execution, timeout, and error recovery | Code execution tool, subprocess sandboxing, error-retry loop |

## Step 1: Build a Code Interpreter Agent

**File:** `starter/code_interpreter.py` (or `.js`)

You will:
1. Implement `execute_python(code, timeout=10)` — runs Python code in a subprocess with timeout and captures stdout/stderr
2. Wire it as a tool: `run_python_code` with JSON Schema accepting a `code` string parameter
3. Build a ReAct agent that can call this tool alongside `search_filings`
4. The agent writes Python to analyze the mock UCC data injected as a variable
5. Test with 3 scenarios:
   - `"Count UCC filings by state and show the results"` — agent writes code to group and count
   - `"Calculate the average number of days until expiration for all active filings"` — agent writes date math
   - `"What percentage of filings have blanket liens vs specific collateral?"` — agent writes string analysis

**Run it:**
```bash
python starter/code_interpreter.py
# or
node starter/code_interpreter.js
```

**Checkpoint:** Each query results in the agent writing Python code, executing it, reading the output, and incorporating the result into its answer. Errors in generated code trigger a retry.

## Verification

```bash
# Python
python solution/code_interpreter.py

# Node.js
node solution/code_interpreter.js
```

Compare your output against `expected_output/sample_output.txt`.

## What You Built

1. **Code execution tool** — a sandboxed Python runner with timeout and output capture
2. **Agent-generated code** — Claude writes Python on the fly to answer analytical questions
3. **Error recovery** — if generated code fails, the error is sent back and Claude fixes it
4. **Hybrid approach** — combining tool-use (search_filings) with code execution for computation

## Next

- **M15B**: Build a Complete Agent & Subagent System — assemble tools, agents, and coordinator into one working system
- **M16**: Input Guardrails — protect your agent from malicious or invalid inputs
