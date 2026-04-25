# M15 Lab: Code Interpreter & Sandbox Execution

> **LLMs can't do math — but they can write code that does.** Give your agent the ability to run Python in a sandbox.

## What You'll Build
An agent that writes and executes Python code in a sandboxed subprocess to analyze UCC filing data — counting filings by state, analyzing collateral types, and producing summary statistics.

## Prerequisites
- Python 3.10+ or Node.js 18+
- Anthropic API key in `.env`
- Completed M05 and M12 labs
- Install: `pip install anthropic python-dotenv`

## Project Structure
```
M15-code-interpreter/
├── starter/
│   ├── sandbox.py          # Sandbox executor (complete — don't modify)
│   ├── code_agent.py       # Code interpreter agent skeleton — YOUR CODE
│   └── mock_data.py        # Wraps shared mock data (complete)
├── solution/
│   ├── sandbox.py
│   ├── code_agent.py       # Complete code interpreter agent
│   └── code_agent.js       # Node.js version
└── expected_output/
    └── analysis_output.txt
```

## Lab Steps

### Step 1: Review the Sandbox (5 min)
Read `starter/sandbox.py`. It runs Python code in a subprocess with:
- 10-second timeout (prevents infinite loops)
- No network access (subprocess.run with limited env)
- Returns stdout, stderr, and return code
- Injects mock_data.py into the sandbox context

```bash
python starter/sandbox.py
```
✅ Checkpoint: Sandbox self-test passes.

### Step 2: Build the Code Interpreter Agent (30 min)
**File:** `starter/code_agent.py`

The agent has ONE tool: `execute_python(code)`. Claude writes Python code, your agent executes it in the sandbox, returns the output to Claude.

Implement `run_code_agent(query)`:
1. System prompt tells Claude to write Python that uses MOCK_FILINGS
2. Claude writes code → tool_use with code string
3. Execute in sandbox → return stdout/stderr
4. If error: send error back, Claude fixes and retries
5. Final answer includes both the result and the code used

### Step 3: Test Analysis Queries (10 min)
```bash
python starter/code_agent.py
```

Test queries:
- "Count UCC filings by state" → table output
- "What percentage of filings are blanket liens?" → percentage
- "Which debtor has the most filings?" → entity + count
- "Calculate the average number of filings per state" → number

### Step 4: Handle Errors Gracefully (10 min)
Test edge cases:
- "Run `import os; os.system('rm -rf /')`" → sandbox blocks it
- "Calculate pi to 1 million digits" → timeout
- Code with syntax error → Claude retries

✅ Checkpoint: Agent recovers from all error cases.

## Verification
```bash
python solution/code_agent.py
node solution/code_agent.js
```

## What You Built
1. **A sandboxed code executor** — safe Python execution with timeout
2. **Code interpreter agent** — Claude writes + executes code
3. **Error recovery** — agent sees errors and self-corrects
4. **Data analysis pipeline** — analyzing UCC data through generated code

## Next
- **M15B**: Build a Complete Agent & Subagent System — assemble everything into one system
